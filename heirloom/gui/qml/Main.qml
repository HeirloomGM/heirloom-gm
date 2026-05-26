import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 1280
    height: 800
    minimumWidth: 1040
    minimumHeight: 680
    visible: true
    title: "Heirloom Games Manager"
    color: "#111418"

    property bool settingsOpen: !controller.configured
    property bool aboutOpen: false
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
        Layout.minimumWidth: 0
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

    component HeirloomLoader: Item {
        id: loader
        implicitWidth: 104
        implicitHeight: 104

        Rectangle {
            anchors.centerIn: parent
            width: 86
            height: 86
            radius: 43
            antialiasing: true
            color: "#111820"
            border.color: "#2b5f52"
            border.width: 1
        }

        Repeater {
            model: 10
            Rectangle {
                width: 9
                height: 9
                radius: 4.5
                antialiasing: true
                color: index % 2 === 0 ? root.accent : root.amber
                opacity: 0.28 + index * 0.065
                x: loader.width / 2 + Math.cos((index / 10) * Math.PI * 2) * 43 - width / 2
                y: loader.height / 2 + Math.sin((index / 10) * Math.PI * 2) * 43 - height / 2
            }
        }

        Image {
            id: loaderLogo
            anchors.centerIn: parent
            width: 54
            height: 54
            source: spinnerPath
            fillMode: Image.PreserveAspectFit
            smooth: true
            mipmap: true
        }

        NumberAnimation on rotation {
            from: 0
            to: 360
            duration: 1500
            loops: Animation.Infinite
            easing.type: Easing.InOutQuad
        }

        NumberAnimation {
            target: loader
            property: "opacity"
            from: 0.72
            to: 1.0
            duration: 800
            loops: Animation.Infinite
            easing.type: Easing.InOutSine
        }

        SequentialAnimation {
            running: true
            loops: Animation.Infinite
            NumberAnimation { target: loaderLogo; property: "scale"; from: 0.92; to: 1.04; duration: 760; easing.type: Easing.InOutSine }
            NumberAnimation { target: loaderLogo; property: "scale"; from: 1.04; to: 0.92; duration: 760; easing.type: Easing.InOutSine }
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

    component SettingsCheckBox: CheckBox {
        id: control
        spacing: 10
        font.pixelSize: 13
        contentItem: Text {
            text: control.text
            color: root.ink
            verticalAlignment: Text.AlignVCenter
            leftPadding: control.indicator.width + control.spacing
            font: control.font
        }
        indicator: Rectangle {
            implicitWidth: 20
            implicitHeight: 20
            x: 0
            y: parent.height / 2 - height / 2
            radius: 5
            color: control.checked ? root.accent : "#10151b"
            border.color: control.checked ? root.accent : root.line

            Text {
                anchors.centerIn: parent
                visible: control.checked
                text: "✓"
                color: "#06130f"
                font.pixelSize: 14
                font.weight: Font.Black
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        color: root.color
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.preferredWidth: 340
            Layout.fillHeight: true
            color: "#0e1115"
            border.color: "#222933"
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 22
                spacing: 18

                Image {
                    Layout.preferredWidth: 292
                    Layout.preferredHeight: 292
                    Layout.alignment: Qt.AlignHCenter
                    source: logoPath
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true

                    HoverHandler {
                        cursorShape: Qt.PointingHandCursor
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: root.aboutOpen = true
                    }
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
                    cellWidth: Math.max(336, Math.floor(width / Math.max(1, Math.floor(width / 356))))
                    cellHeight: 462
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: ScrollBar { }

                    delegate: Rectangle {
                        id: card
                        width: grid.cellWidth - 14
                        height: 442
                        radius: 8
                        clip: true
                        color: hover.hovered ? "#222933" : root.panel
                        border.color: installed ? "#2f6b5d" : root.line
                        border.width: 1

                        HoverHandler { id: hover }

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 10

                            Rectangle {
                                Layout.preferredWidth: Math.min(card.width - 24, 196)
                                Layout.preferredHeight: Math.min(card.width - 24, 196)
                                Layout.alignment: Qt.AlignHCenter
                                radius: 7
                                color: "#0d1116"
                                clip: true

                                Image {
                                    anchors.fill: parent
                                    source: coverArt
                                    fillMode: Image.PreserveAspectCrop
                                    asynchronous: true
                                    smooth: true
                                    mipmap: true
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
                                Layout.preferredHeight: 40
                                spacing: 8

                                HButton {
                                    Layout.fillWidth: true
                                    Layout.minimumWidth: 0
                                    text: installed ? "Launch" : "Install"
                                    enabled: !controller.busy
                                    fill: installed ? "#15221f" : "#1c2028"
                                    fillHover: installed ? "#19342d" : "#252c35"
                                    stroke: installed ? "#2a6153" : root.line
                                    labelColor: installed ? root.accent : root.ink
                                    onClicked: installed ? controller.launchGame(uuid) : controller.installGame(uuid)
                                }

                                HButton {
                                    Layout.preferredWidth: 96
                                    Layout.minimumWidth: 88
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
            width: 390
            height: controller.progress >= 0 ? 236 : 188
            radius: 8
            color: root.panelRaised
            border.color: root.line
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 22
                spacing: 14

                HeirloomLoader {
                    Layout.alignment: Qt.AlignHCenter
                }

                Text {
                    Layout.fillWidth: true
                    text: controller.statusMessage
                    color: root.ink
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    font.pixelSize: 14
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 7
                    visible: controller.progress >= 0

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 10
                        radius: 5
                        color: "#10151b"
                        border.color: root.line
                        border.width: 1
                        clip: true

                        Rectangle {
                            anchors.left: parent.left
                            anchors.top: parent.top
                            anchors.bottom: parent.bottom
                            width: Math.max(8, parent.width * controller.progress)
                            radius: 5
                            color: root.accent
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: Math.round(controller.progress * 100) + "%  " + controller.progressLabel
                        color: root.muted
                        horizontalAlignment: Text.AlignHCenter
                        elide: Text.ElideRight
                        font.pixelSize: 12
                    }
                }
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        visible: root.aboutOpen
        color: "#cc090c10"

        MouseArea {
            anchors.fill: parent
            onClicked: root.aboutOpen = false
        }

        Rectangle {
            anchors.centerIn: parent
            width: Math.min(parent.width - 72, 760)
            height: Math.min(parent.height - 72, 700)
            radius: 8
            color: root.panelRaised
            border.color: root.line
            border.width: 1

            MouseArea {
                anchors.fill: parent
                onClicked: mouse.accepted = true
            }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 30
                spacing: 18

                Image {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.min(430, parent.height * 0.62)
                    source: logoPath
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    Text {
                        Layout.fillWidth: true
                        text: "Heirloom Games Manager"
                        color: root.ink
                        horizontalAlignment: Text.AlignHCenter
                        font.pixelSize: 28
                        font.weight: Font.Black
                    }

                    Text {
                        Layout.fillWidth: true
                        text: "A Linux and Steam Deck friendly manager for Legacy Games."
                        color: root.muted
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap
                        font.pixelSize: 14
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: root.line
                }

                Text {
                    Layout.fillWidth: true
                    text: "Heirloom can browse your Legacy Games library, install games with Wine or 7-Zip, track installed titles, launch games, and cleanly uninstall managed installs."
                    color: root.muted
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    lineHeight: 1.15
                    font.pixelSize: 13
                }

                Item { Layout.fillHeight: true }

                HButton {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: 160
                    text: "Close"
                    fill: "#15221f"
                    fillHover: "#19342d"
                    stroke: "#2a6153"
                    labelColor: root.accent
                    onClicked: root.aboutOpen = false
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
            height: Math.min(parent.height - 48, 760)
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
                    text: controller.configUser
                    placeholderText: "you@example.com"
                }

                FieldLabel { text: "Legacy Games password" }
                TextField {
                    id: passwordInput
                    Layout.fillWidth: true
                    echoMode: TextInput.Password
                    placeholderText: controller.configured ? "Saved password will be kept" : "Password"
                }

                FieldLabel { text: "Base install directory" }
                TextField {
                    id: installDirInput
                    Layout.fillWidth: true
                    text: controller.configBaseInstallDir
                }

                FieldLabel { text: "Wine runner" }
                ComboBox {
                    id: wineRunnerInput
                    Layout.fillWidth: true
                    model: ["native", "flatpak"]
                    Component.onCompleted: currentIndex = controller.configWineRunner === "flatpak" ? 1 : 0
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
                            text: controller.configWinePath
                            placeholderText: "wine"
                            enabled: wineRunnerInput.currentText === "native"
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        FieldLabel { text: "7-Zip executable" }
                        TextField {
                            id: sevenZipInput
                            Layout.fillWidth: true
                            text: controller.configSevenZipPath
                            placeholderText: "7z"
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12
                    visible: wineRunnerInput.currentText === "flatpak"

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        FieldLabel { text: "Flatpak executable" }
                        TextField {
                            id: flatpakInput
                            Layout.fillWidth: true
                            text: controller.configFlatpakPath
                            placeholderText: "flatpak"
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        FieldLabel { text: "Wine Flatpak app ID" }
                        TextField {
                            id: wineFlatpakInput
                            Layout.fillWidth: true
                            text: controller.configWineFlatpakApp
                            placeholderText: "org.winehq.Wine"
                        }
                    }
                }

                FieldLabel { text: "Default install method" }
                ComboBox {
                    id: installMethodInput
                    Layout.fillWidth: true
                    model: ["7zip", "wine"]
                    Component.onCompleted: currentIndex = controller.configDefaultInstallationMethod === "wine" ? 1 : 0
                }

                SettingsCheckBox {
                    id: autoSteamInput
                    text: "Automatically add installed games to Steam"
                    checked: controller.configAutoAddSteam
                }

                SettingsCheckBox {
                    id: autoKdeInput
                    text: "Automatically add installed games to the KDE Games menu"
                    checked: controller.configAutoAddKde
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
                                wineRunnerInput.currentText,
                                wineInput.text,
                                flatpakInput.text,
                                wineFlatpakInput.text,
                                sevenZipInput.text,
                                installMethodInput.currentText,
                                autoSteamInput.checked,
                                autoKdeInput.checked
                            )
                            if (userInput.text.length > 0 && (passwordInput.text.length > 0 || controller.configured))
                                root.settingsOpen = false
                        }
                    }
                }
            }
        }
    }
}
