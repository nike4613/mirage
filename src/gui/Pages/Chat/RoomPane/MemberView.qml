// SPDX-License-Identifier: LGPL-3.0-or-later

import QtQuick 2.12
import QtQuick.Layouts 1.12
import "../../.."
import "../../../Base"

HColumnLayout {
    readonly property alias keybindFocusItem: filterField
    readonly property var modelSyncId:
        [chat.userId, chat.roomId, "filtered_members"]

    HListView {
        id: memberList
        clip: true

        model: ModelStore.get(modelSyncId)

        delegate: MemberDelegate {
            id: member
            width: memberList.width
        }

        Layout.fillWidth: true
        Layout.fillHeight: true

        Rectangle {
            anchors.fill: parent
            z: -100
            color: theme.chat.roomPane.listView.background
        }
    }

    Rectangle {
        color: theme.chat.roomPane.bottomBar.background

        Layout.fillWidth: true
        Layout.minimumHeight: theme.baseElementsHeight
        Layout.maximumHeight: Layout.minimumHeight

        HRowLayout {
            anchors.fill: parent

            HTextField {
                id: filterField
                saveName: "memberFilterField"
                saveId: chat.roomId

                backgroundColor:
                    theme.chat.roomPane.bottomBar.filterMembers.background
                bordered: false
                opacity: width >= 16 * theme.uiScale ? 1 : 0

                Layout.fillWidth: true
                Layout.fillHeight: true

                // FIXME: fails to display sometimes for some reason if
                // declared normally
                Component.onCompleted: placeholderText = qsTr("Filter members")

                onTextChanged:
                    py.callCoro("set_substring_filter", [modelSyncId, text])

                Keys.onEscapePressed: {
                    roomPane.toggleFocus()
                    if (window.settings.clearMemberFilterOnEscape) text = ""
                }

                Behavior on opacity { HNumberAnimation {} }
            }

            HButton {
                id: inviteButton
                icon.name: "room-send-invite"
                backgroundColor:
                    theme.chat.roomPane.bottomBar.inviteButton.background
                enabled: chat.roomInfo.can_invite

                toolTip.text:
                    enabled ?
                    qsTr("Invite members to this room") :
                    qsTr("No permission to invite members to this room")

                onClicked: utils.makePopup(
                    "Popups/InviteToRoomPopup.qml",
                    chat,
                    {
                        userId: chat.userId,
                        roomId: chat.roomId,
                        roomName: chat.roomInfo.display_name,
                        invitingAllowed:
                            Qt.binding(() => inviteButton.enabled),
                    },
                )

                Layout.fillHeight: true

                HShortcut {
                    sequences: window.settings.keys.inviteToRoom
                    onActivated: inviteButton.clicked()
                }
            }
        }
    }
}
