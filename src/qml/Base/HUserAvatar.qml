import QtQuick 2.7

HAvatar {
    property string userId: ""

    readonly property var userInfo: userId ? users.getUser(userId) : ({})
    name: userInfo.displayName || userId.substring(1)  // no leading @
    imageUrl: userInfo.avatarUrl

    //HImage {
        //id: status
        //anchors.right: parent.right
        //anchors.bottom: parent.bottom
        //source: "../../icons/status.svg"
        //sourceSize.width: 12
    //}
}