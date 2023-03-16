*** Settings ***
Library   RemoteSwingLibrary
Library    Screenshot
Test Tags       regress2  web
# Resource  ../resource.robot    # outside of repo. Contains real username and password

*** Variables ***
${checkBoxIndex}        0
${fileChooserButton}    Choose PDF
${fileToChoose}         test_file2.pdf
${labelContent}         Report type:
${listIndex}            0


*** Test Cases ***
ChooseFileFromFileChooserv2245
    Start Application    my_app    ${EXECDIR}/verapdf/verapdf-gui  
    Select Main Window
    List Components In Context
    pushButton    ${fileChooserButton}
    chooseFromFileChooser    ${fileToChoose}
    Select Dialog    regexp=Error.*
    List Components In Context
    # pushButton    OptionPane.button
    Take Screenshot  OkButton
    pushButton    OK
    [Teardown]    System Exit