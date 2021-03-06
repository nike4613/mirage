// SPDX-License-Identifier: LGPL-3.0-or-later

import QtQuick 2.12
import QtQuick.Layouts 1.12
import ".."

HLabel {
    font.pixelSize: theme.fontSize.small
    verticalAlignment: Qt.AlignVCenter
    color: theme.colors.halfDimText
    visible: Layout.maximumWidth > 0

    Layout.fillHeight: true
    Layout.maximumWidth:
        text && tile.width >= 200 * theme.uiScale ?
        implicitWidth : 0


    property HTile tile


    Behavior on Layout.maximumWidth { HNumberAnimation {} }
}
