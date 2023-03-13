*** Settings ***
Library     RemoteSwingLibrary
# Resource    ../resource.robot    # outside of repo. Contains real username and password


*** Variables ***
${checkBoxIndex}        0
${fileChooserButton}    Choose PDF
${fileToChoose}         test_file2.pdf
${labelContent}         Report type:
${listIndex}            0
${veraPATH}             ${EXECDIR}/verapdf


*** Test Cases ***
Choose File From File Chooser
    Log    ${CURDIR}
    Log    ${EXECDIR}
    Log    ${veraPATH}


Choose File From File Chooser v2
    Log    CURDIR:    ${CURDIR}
    Log    EXECDIR:    ${EXECDIR}
    Log    veraPATH:    ${veraPATH}