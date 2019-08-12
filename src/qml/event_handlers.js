"use strict"


function onExitRequested(exitCode) {
    Qt.exit(exitCode)
}


function onCoroutineDone(uuid, result) {
    py.pendingCoroutines[uuid](result)
    delete pendingCoroutines[uuid]
}


function onModelUpdated(syncId, data, serializedSyncId) {
    window.modelSources[serializedSyncId] = data
    window.modelSourcesChanged()
}