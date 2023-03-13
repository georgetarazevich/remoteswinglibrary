*** Settings ***
Library   RemoteSwingLibrary
# Resource  ../resource.robot    # outside of repo. Contains real username and password

*** Variables ***
${checkBoxIndex}        0
${fileChooserButton}    Choose PDF
${fileToChoose}         test_file2.pdf
${labelContent}         Report type:
${listIndex}            0


*** Test Cases ***
Choose File From File Chooser
    Start Application    my_app    java -jar ./verapdf/bin/greenfield-apps-1.23.147.jar 5 seconds
    Select Main Window
    List Components In Context
    pushButton    ${fileChooserButton}
    chooseFromFileChooser    ${fileToChoose}
    Select Dialog    regexp=Error.*
    List Components In Context
    # pushButton    OptionPane.button
    pushButton    OK
    [Teardown]    System Exit

Choose File From File Chooser v2
    Start Application    my_app    verapdf/verapdf-gui 5 seconds
    Select Main Window
    List Components In Context
    pushButton    ${fileChooserButton}
    chooseFromFileChooser    ${fileToChoose}
    Select Dialog    regexp=Error.*
    List Components In Context
    # pushButton    OptionPane.button
    pushButton    OK
    [Teardown]    System Exit

# *** Test Cases ***
# Connecting to another machine
#    Open Connection   ${REMOTEIP}
#    Login     ${USERNAME}  ${PASSWORD}
#    Put File  ${REMOTESWINGLIBRARYPATH}   remoteswinglibrary.jar
#    Write     xvfb-run java -javaagent:remoteswinglibrary.jar=${MYIP}:${REMOTESWINGLIBRARYPORT}:DEBUG -jar remoteswinglibrary.jar
#    Application Started    myjar   timeout=5 seconds
#    System Exit
#    [Teardown]   Tearing

# *** Keywords ***
# Tearing
#    Read
#    Close All Connections
