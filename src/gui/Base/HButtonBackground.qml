// SPDX-License-Identifier: LGPL-3.0-or-later

import QtQuick 2.12
import QtQuick.Controls 2.12

Rectangle {
    color: buttonTheme.background
    opacity: loading ? theme.loadingElementsOpacity :
             enabled ? 1 : theme.disabledElementsOpacity


    property var button
    property QtObject buttonTheme


    Behavior on opacity { HNumberAnimation {} }


    Rectangle {
        anchors.fill: parent
        radius: parent.radius
        color: button.checked ? buttonTheme.checkedOverlay :

               button.enabled && button.pressed ? buttonTheme.pressedOverlay :

               (button.enabled && button.hovered) || button.activeFocus ?
               buttonTheme.hoveredOverlay :

               "transparent"

        Behavior on color { HColorAnimation { factor: 0.5 } }
    }
}
