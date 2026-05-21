import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 1280
    height: 800
    minimumWidth: 980
    minimumHeight: 680
    visible: true
    title: "Heirloom Games Manager"
    color: "#111418"

    property bool settingsOpen: !controller.configured
    property color ink: "#f5f7fb"
    property color muted: "#a6b0bf"
    property color panel: "#171b21"
    property color panelRaised: "#20262e"
    property color line: "#313946"
    property color accent: "#33d6a6"
    property color amber: "#e8b04b"
    property color danger: "#ef6b73"

    component HButton: Button {
        id: control
        property color fill: root.panelRaised
        property color fillHover: "#2a323d"
        property color stroke: root.line
        property color labelColor: root.ink
        padding: 10
        leftPadding: 16
        rightPadding: 16
        implicitHeight: 40
        font.pixelSize: 14
        font.weight: Font.DemiBold
        contentItem: Text {
            text: control.text
            color: control.enabled ? control.labelColor : "#727b89"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            font: control.font
        }
        background: Rectangle {
            radius: 7
            color: control.hovered ? control.fillHover : control.fill
            border.color: control.stroke
            border.width: 1
        }
    }

    component FilterButton: Button {
        id: control
        property bool selected: false
        padding: 8
        leftPadding: 12
        rightPadding: 12
        implicitHeight: 36
        font.pixelSize: 13
        font.weight: Font.DemiBold
        contentItem: Text {
            text: control.text
            color: control.selected ? "#06130f" : root.muted
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            font: control.font
        }
        background: Rectangle {
            radius: 7
            color: control.selected ? root.accent : (control.hovered ? "#252c35" : "#151a20")
            border.color: control.selected ? root.accent : root.line
            border.width: 1
        }
    }

    component SectionLabel: Text {
        color: root.muted
        font.pixelSize: 11
        font.weight: Font.DemiBold
        textFormat: Text.PlainText
    }

    component FieldLabel: Text {
        color: root.muted
        font.pixelSize: 12
        font.weight: Font.DemiBold
    }

    Rectangle {
        anchors.fill: parent
        color: root.color
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.preferredWidth: 286
            Layout.fillHeight: true
            color: "#0e1115"
            border.color: "#222933"
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 22
                spacing: 18

                Image {
                    Layout.preferredWidth: 132
                    Layout.preferredHeight: 132
                    Layout.alignment: Qt.AlignHCenter
                    source: logoPath
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4

                    Text {
                        Layout.fillWidth: true
                        text: "Heirloom"
                        color: root.ink
                        horizontalAlignment: Text.AlignHCenter
                        font.pixelSize: 30
                        font.weight: Font.Black
                    }

                    Text {
                        Layout.fillWidth: true
                        text: "Games Manager"
                        color: root.muted
                        horizontalAlignment: Text.AlignHCenter
                        font.pixelSize: 14
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: root.line
                }

                SectionLabel { text: "LIBRARY" }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    HButton {
                        Layout.fillWidth: true
                        text: "Refresh Library"
                        enabled: controller.configured && !controller.busy
                        fill: "#15221f"
                        fillHover: "#19342d"
                        stroke: "#2a6153"
                        labelColor: root.accent
                        onClicked: controller.refreshLibrary()
                    }

                    HButton {
                        Layout.fillWidth: true
                        text: "Settings"
                        enabled: !controller.busy
                        onClicked: root.settingsOpen = true
                    }
                }

                SectionLabel { text: "FILTER" }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    FilterButton {
                        Layout.fillWidth: true
                        text: "All Games"
                        selected: filterGroup.mode === "all"
                        onClicked: {
                            filterGroup.mode = "all"
                            controller.setFilterMode("all")
                        }
                    }

                    FilterButton {
                        Layout.fillWidth: true
                        text: "Installed"
                        selected: filterGroup.mode === "installed"
                        onClicked: {
                            filterGroup.mode = "installed"
                            controller.setFilterMode("installed")
                        }
                    }

                    FilterButton {
                        Layout.fillWidth: true
                        text: "Not Installed"
                        selected: filterGroup.mode === "notInstalled"
                        onClicked: {
                            filterGroup.mode = "notInstalled"
                            controller.setFilterMode("notInstalled")
                        }
                    }

                    QtObject {
                        id: filterGroup
                        property string mode: "all"
                    }
                }

                Item { Layout.fillHeight: true }

                Rectangle {
                    Layout.fillWidth: true
                    radius: 7
                    color: "#14191f"
                    border.color: root.line
                    border.width: 1

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 6

                        Text {
                            Layout.fillWidth: true
                            text: controller.busy ? "Working" : "Status"
                            color: root.muted
                            font.pixelSize: 12
                            font.weight: Font.DemiBold
                        }

                        Text {
                            Layout.fillWidth: true
                            text: controller.errorMessage.length > 0 ? controller.errorMessage : controller.statusMessage
                            color: controller.errorMessage.length > 0 ? root.danger : root.ink
                            wrapMode: Text.WordWrap
                            font.pixelSize: 13
                            lineHeight: 1.15
                        }
                    }
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 86
                color: "#15191f"
                border.color: "#242b35"
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 28
                    anchors.rightMargin: 28
                    spacing: 18

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        Text {
                            text: "Library"
                            color: root.ink
                            font.pixelSize: 26
                            font.weight: Font.Black
                        }

                        Text {
                            text: "Browse, install, launch, and cleanly remove your Legacy Games collection."
                            color: root.muted
                            font.pixelSize: 13
                        }
                    }

                    Rectangle {
                        Layout.preferredWidth: 340
                        Layout.preferredHeight: 42
                        radius: 7
                        color: "#0f1318"
                        border.color: root.line
                        border.width: 1

                        TextInput {
                            id: searchField
                            anchors.fill: parent
                            anchors.leftMargin: 14
                            anchors.rightMargin: 14
                            color: root.ink
                            selectionColor: root.accent
                            selectedTextColor: "#07110f"
                            verticalAlignment: TextInput.AlignVCenter
                            font.pixelSize: 14
                            clip: true
                            onTextChanged: controller.setSearch(text)
                        }

                        Text {
                            anchors.left: parent.left
                            anchors.leftMargin: 14
                            anchors.verticalCenter: parent.verticalCenter
                            text: "Search games"
                            color: "#707987"
                            font.pixelSize: 14
                            visible: searchField.text.length === 0
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: root.color

                GridView {
                    id: grid
                    anchors.fill: parent
                    anchors.margins: 22
                    model: gamesModel
                    clip: true
                    cellWidth: Math.max(300, Math.floor(width / Math.max(1, Math.floor(width / 330))))
                    cellHeight: 394
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: ScrollBar { }

                    delegate: Rectangle {
                        id: card
                        width: grid.cellWidth - 14
                        height: 374
                        radius: 8
                        color: hover.hovered ? "#222933" : root.panel
                        border.color: installed ? "#2f6b5d" : root.line
                        border.width: 1

                        HoverHandler { id: hover }

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 10

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 164
                                radius: 7
                                color: "#0d1116"
                                clip: true

                                Image {
                                    anchors.fill: parent
                                    source: coverArt
                                    fillMode: Image.PreserveAspectCrop
                                    asynchronous: true
                                    smooth: true
                                }

                                Rectangle {
                                    anchors.left: parent.left
                                    anchors.top: parent.top
                                    anchors.margins: 10
                                    radius: 6
                                    color: installed ? root.accent : root.amber
                                    height: 26
                                    width: statusText.implicitWidth + 18

                                    Text {
                                        id: statusText
                                        anchors.centerIn: parent
                                        text: installed ? "INSTALLED" : "READY"
                                        color: "#07110f"
                                        font.pixelSize: 11
                                        font.weight: Font.Black
                                    }
                                }
                            }

                            Text {
                                Layout.fillWidth: true
                                text: title
                                color: root.ink
                                font.pixelSize: 18
                                font.weight: Font.Black
                                elide: Text.ElideRight
                            }

                            Text {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 62
                                text: description
                                color: root.muted
                                font.pixelSize: 13
                                lineHeight: 1.14
                                wrapMode: Text.WordWrap
                                elide: Text.ElideRight
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 32
                                    radius: 6
                                    color: "#11161c"
                                    border.color: root.line
                                    border.width: 1

                                    Text {
                                        anchors.centerIn: parent
                                        text: installedSize.length > 0 ? installedSize : "Size unknown"
                                        color: root.muted
                                        font.pixelSize: 12
                                        elide: Text.ElideRight
                                    }
                                }
                            }

                            Item { Layout.fillHeight: true }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8

                                HButton {
                                    Layout.fillWidth: true
                                    text: installed ? "Launch" : "Install"
                                    enabled: !controller.busy
                                    fill: installed ? "#15221f" : "#1c2028"
                                    fillHover: installed ? "#19342d" : "#252c35"
                                    stroke: installed ? "#2a6153" : root.line
                                    labelColor: installed ? root.accent : root.ink
                                    onClicked: installed ? controller.launchGame(uuid) : controller.installGame(uuid)
                                }

                                HButton {
                                    Layout.preferredWidth: 104
                                    text: "Uninstall"
                                    visible: installed
                                    enabled: !controller.busy
                                    fill: "#28191d"
                                    fillHover: "#3a2026"
                                    stroke: "#67333c"
                                    labelColor: root.danger
                                    onClicked: controller.uninstallGame(uuid)
                                }
                            }
                        }
                    }

                    Text {
                        anchors.centerIn: parent
                        visible: grid.count === 0 && !controller.busy
                        text: controller.configured ? "No games match the current view." : "Configure Heirloom to load your library."
                        color: root.muted
                        font.pixelSize: 16
                    }
                }
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        visible: controller.busy
        color: "#99090c10"

        Rectangle {
            anchors.centerIn: parent
            width: 360
            height: 132
            radius: 8
            color: root.panelRaised
            border.color: root.line
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 22
                spacing: 14

                BusyIndicator {
                    Layout.alignment: Qt.AlignHCenter
                    running: controller.busy
                }

                Text {
                    Layout.fillWidth: true
                    text: controller.statusMessage
                    color: root.ink
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    font.pixelSize: 14
                }
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        visible: root.settingsOpen
        color: "#cc090c10"

        MouseArea {
            anchors.fill: parent
            onClicked: {
                if (controller.configured)
                    root.settingsOpen = false
            }
        }

        Rectangle {
            anchors.centerIn: parent
            width: Math.min(parent.width - 48, 560)
            height: 620
            radius: 8
            color: root.panelRaised
            border.color: root.line
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 28
                spacing: 14

                Text {
                    text: "Configuration"
                    color: root.ink
                    font.pixelSize: 26
                    font.weight: Font.Black
                }

                Text {
                    Layout.fillWidth: true
                    text: "Connect Heirloom to your Legacy Games account and choose where installed games should live."
                    color: root.muted
                    font.pixelSize: 14
                    wrapMode: Text.WordWrap
                }

                FieldLabel { text: "Legacy Games email or username" }
                TextField {
                    id: userInput
                    Layout.fillWidth: true
                    placeholderText: "you@example.com"
                }

                FieldLabel { text: "Legacy Games password" }
                TextField {
                    id: passwordInput
                    Layout.fillWidth: true
                    echoMode: TextInput.Password
                    placeholderText: "Password"
                }

                FieldLabel { text: "Base install directory" }
                TextField {
                    id: installDirInput
                    Layout.fillWidth: true
                    text: "~/Games/LegacyGames/"
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        FieldLabel { text: "Wine executable" }
                        TextField {
                            id: wineInput
                            Layout.fillWidth: true
                            placeholderText: "wine"
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        FieldLabel { text: "7-Zip executable" }
                        TextField {
                            id: sevenZipInput
                            Layout.fillWidth: true
                            placeholderText: "7z"
                        }
                    }
                }

                FieldLabel { text: "Default install method" }
                ComboBox {
                    id: installMethodInput
                    Layout.fillWidth: true
                    model: ["7zip", "wine"]
                }

                Item { Layout.fillHeight: true }

                Text {
                    Layout.fillWidth: true
                    visible: controller.errorMessage.length > 0
                    text: controller.errorMessage
                    color: root.danger
                    wrapMode: Text.WordWrap
                    font.pixelSize: 13
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    HButton {
                        Layout.fillWidth: true
                        text: "Cancel"
                        visible: controller.configured
                        enabled: !controller.busy
                        onClicked: root.settingsOpen = false
                    }

                    HButton {
                        Layout.fillWidth: true
                        text: "Save And Refresh"
                        enabled: !controller.busy
                        fill: "#15221f"
                        fillHover: "#19342d"
                        stroke: "#2a6153"
                        labelColor: root.accent
                        onClicked: {
                            controller.saveConfiguration(
                                userInput.text,
                                passwordInput.text,
                                installDirInput.text,
                                wineInput.text,
                                sevenZipInput.text,
                                installMethodInput.currentText
                            )
                            if (userInput.text.length > 0 && passwordInput.text.length > 0)
                                root.settingsOpen = false
                        }
                    }
                }
            }
        }
    }
}
