from __future__ import with_statement
from contextlib import contextmanager
import os
import threading
import time
import SocketServer
from xmlrpclib import ProtocolError
from robot.errors import HandlerExecutionFailed, TimeoutError
from robot.libraries.Process import Process
from robot.libraries.Remote import Remote
from robot.running import EXECUTION_CONTEXTS
from robot.running.namespace import IMPORTER
from robot.running.testlibraries import TestLibrary
from robot.libraries.BuiltIn import BuiltIn
from robot.api import logger

REMOTE_AGENTS_LIST = []
EXPECTED_AGENT_RECEIVED = threading.Event()

class SimpleServer(SocketServer.BaseRequestHandler):

    def handle(self):
        data = ''.join(iter(self.read_socket, ''))
        print '*DEBUG:%d* Registered java rappio agent at port %s' % (time.time()*1000, data.decode())
        REMOTE_AGENTS_LIST.append(data.decode())
        EXPECTED_AGENT_RECEIVED.set()
        self.request.sendall(data)

    def read_socket(self):
        return self.request.recv(1)


class InvalidURLException(Exception):
    pass


class _RobotImporterWrapper(object):
    def remove_library(self, name, args):
        lib = TestLibrary(name, args, None, create_handlers=False)
        key = (name, lib.positional_args, lib.named_args)
        self._remove_library(key)

    def _remove_library(self, key):
        raise NotImplementedError()


class Robot26ImporterWrapper(_RobotImporterWrapper):
    def _remove_library(self, key):
        if key in IMPORTER._library_cache:
            index = IMPORTER._library_cache._keys.index(key)
            IMPORTER._library_cache._keys.pop(index)
            IMPORTER._library_cache._items.pop(index)


class OldRobotImporterWrapper(_RobotImporterWrapper):
    def _remove_library(self, key):
        if IMPORTER._libraries.has_key(key):  # key in dict doesn't work here
            index = IMPORTER._libraries._keys.index(key)
            IMPORTER._libraries._keys.pop(index)
            IMPORTER._libraries._libs.pop(index)


class RobotLibraryImporter(object):
    """Class for manipulating Robot Framework library imports during runtime"""

    def re_import_rappio(self):
        name = 'Rappio'
        self._remove_lib_from_current_namespace(name)
        self._import_wrapper().remove_library(name, [])
        BuiltIn().import_library(name)

    def _import_wrapper(self):
        if hasattr(IMPORTER, '_library_cache'):
            return Robot26ImporterWrapper()
        return OldRobotImporterWrapper()

    def _remove_lib_from_current_namespace(self, name):
        testlibs = EXECUTION_CONTEXTS.current.namespace._testlibs
        if testlibs.has_key(name):
            del(testlibs[name])


class RappioTimeoutError(RuntimeError):
    pass


class Rappio(object):
    """Robot Framework library leveraging Java-agents to run SwingLibrary keywords on Java-processes. The library contains
    a simple socket server to communicate with Java agents. When taking the library into use, you can specify the port this
    server uses. Providing the port is optional. If you do not provide one, Rappio will ask the OS for an unused port.

    Examples:
    | Library | Rappio |      |
    | Library | Rappio | 8181 |
    """

    ROBOT_LIBRARY_SCOPE = 'SUITE'
    KEYWORDS = ['system_exit', 'start_application', 'application_started', 'switch_to_application',
                'ensure_application_should_close']
    REMOTES = {}
    CURRENT = None
    PROCESS = Process()
    ROBOT_NAMESPACE_BRIDGE = RobotLibraryImporter()
    TIMEOUT = 60
    PORT = None
    AGENT_PATH = os.path.abspath(os.path.dirname(__file__))

    def __init__(self, port=None):
        if Rappio.PORT is None:
            Rappio.PORT = self._start_port_server(port or 0)
        self._set_env()

    @property
    def current(self):
        if not self.CURRENT:
            return None
        return self.REMOTES[self.CURRENT][0]

    def _start_port_server(self, port):
        address = ('127.0.0.1', int(port))
        server = SocketServer.TCPServer(address, SimpleServer)
        server.allow_reuse_address = True
        t = threading.Thread(target=server.serve_forever)
        t.setDaemon(True)
        t.start()
        return server.server_address[1]

    def _set_env(self):
        agent_command = '-javaagent:%s=%s' % (Rappio.AGENT_PATH, Rappio.PORT)
        os.environ['JAVA_TOOL_OPTIONS'] = agent_command
        logger.info(agent_command)

    def start_application(self, alias, command, timeout=60):
        """Starts the process in the `command` parameter  on the host operating system. The given alias is stored to identify the started application in Rappio."""
        EXPECTED_AGENT_RECEIVED.clear() # We are going to wait for a specific agent
        self.PROCESS.start_process(command, alias=alias, shell=True)
        try:
            self.application_started(alias, timeout=timeout)
        except:
            raise
            result = self.PROCESS.wait_for_process(timeout=0.01)
            logger.info('STDOUT: %s' % result.stdout)
            logger.info('STDERR: %s' % result.stderr)
            raise

    def application_started(self, alias, timeout=60):
        """Detects new Rappio Java-agents in applications that are started without using the Start Application -keyword. The given alias is stored to identify the started application in Rappio.
        Subsequent keywords will be passed on to this application."""
        self.TIMEOUT = int(timeout)
        port = self._get_agent_port()
        url = '127.0.0.1:%s'%port
        self.REMOTES[alias] = [Remote(url+e) for e in ['', '/rappioservices']]
        Rappio.CURRENT = alias
        self.ROBOT_NAMESPACE_BRIDGE.re_import_rappio()

    def _get_agent_port(self):
        if not REMOTE_AGENTS_LIST:
            EXPECTED_AGENT_RECEIVED.clear()
        EXPECTED_AGENT_RECEIVED.wait(
            timeout=self.TIMEOUT) # Ensure that a waited agent is the one we are receiving and not some older one
        if not EXPECTED_AGENT_RECEIVED.isSet():
            raise RappioTimeoutError('Agent port not received before timeout')
        return REMOTE_AGENTS_LIST.pop()

    def _ping_until_timeout(self, timeout):
        timeout = float(timeout)
        delta = min(0.1, timeout)
        endtime = timeout+time.time()
        while endtime > time.time():
            self._run_from_rappioservices(Rappio.CURRENT, 'ping')
            time.sleep(delta)

    def _run_from_rappioservices(self, alias, kw, *args, **kwargs):
        self.REMOTES[alias][1].run_keyword(kw, args, kwargs)

    def ensure_application_should_close(self, timeout, kw, *args):
        with self._run_and_ignore_connection_lost():
            BuiltIn().run_keyword(kw, *args)
        try:
            self._application_should_be_closed(timeout=timeout)
        except RappioTimeoutError, t:
            logger.warn('Application is not closed before timeout - killing application')
            self._take_screenshot()
            self.system_exit(Rappio.CURRENT)
            raise

    def _take_screenshot(self):
        filepath = 'screenshot%s.png' % time.time()
        self._run_from_rappioservices(Rappio.CURRENT, 'takeScreenshot', filepath)
        logger.info('<img src="%s"></img>' % filepath, html=True)

    def _application_should_be_closed(self, timeout):
        with self._run_and_ignore_connection_lost():
            self._ping_until_timeout(timeout)
            raise RappioTimeoutError('Application was not closed before timeout')

    @contextmanager
    def _run_and_ignore_connection_lost(self):
        try:
            yield
        except RuntimeError, r: # disconnection from remotelibrary
            if 'Connection to remote server broken:' in r.message:
                logger.info('Connection died as expected')
                return
            raise
        except HandlerExecutionFailed, e: # disconnection from xmlrpc wrapped in robot keyword
            if 'Connection to remote server broken:' in e.message:
                logger.info('Connection died as expected')
                return
            raise
        except ProtocolError, r: # disconnection from xmlrpc in jython on some platforms
            logger.info('Connection died as expected')
            return

    def system_exit(self, alias, exit_code=1):
        with self._run_and_ignore_connection_lost():
            self._run_from_rappioservices(alias, 'systemExit', exit_code)

    def switch_to_application(self, alias):
        """Switches between Java-agents in applications that are known to Rappio. The application is identified using the alias.
        Subsequent keywords will be passed on to this application."""
        Rappio.CURRENT = alias
        self.ROBOT_NAMESPACE_BRIDGE.re_import_rappio()

    # HYBRID KEYWORDS

    def get_keyword_names(self):
        if self.current:
            return Rappio.KEYWORDS + [kw for
                                      kw in self.current.get_keyword_names(attempts=Rappio.TIMEOUT)
                                      if kw != 'startApplication']
        return Rappio.KEYWORDS

    def __getattr__(self, name):
        current = self.current
        def func(*args, **kwargs):
            return current.run_keyword(name, args, kwargs)
        return func
