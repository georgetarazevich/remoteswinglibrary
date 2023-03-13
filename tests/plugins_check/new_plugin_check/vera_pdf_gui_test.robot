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
    Start Application    my_app  ${EXECDIR}/verapdf/verapdf --version
    [Teardown]    System Exit

Choose File From File Chooser v2
    Start Application    my_app    ${EXECDIR}/verapdf/verapdf-gui 5 seconds
    Select Main Window
    List Components In Context
    pushButton    ${fileChooserButton}
    chooseFromFileChooser    ${fileToChoose}
    Select Dialog    regexp=Error.*
    List Components In Context
    # pushButton    OptionPane.button
    pushButton    OK
    [Teardown]    System Exit