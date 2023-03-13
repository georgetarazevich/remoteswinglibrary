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
Checking logs
    Log    ${CURDIR}
    Log    ${EXECDIR}
    Log    ${veraPATH}
