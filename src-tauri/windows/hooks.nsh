!include "FileFunc.nsh"

!macro NSIS_HOOK_PREINSTALL
  ; Normalize the selected install directory to a leaf app folder before NSIS
  ; copies files and writes the uninstaller.
  ${GetFileName} "$INSTDIR" $0
  StrCmp $0 "cybrtech" done
  StrCpy $INSTDIR "$INSTDIR\cybrtech"
done:
!macroend
