import webbrowser

from PySide6.QtCore import (
    Qt,
    QTimer,
)

from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)


class YouTubeQueueWindow(QDialog):
    def __init__(
        self,
        discord_client,
        guild_id_provider,
        options_provider,
        parent=None,
    ):
        super().__init__(parent)

        self.discord = discord_client
        self.guild_id_provider = guild_id_provider
        self.options_provider = options_provider

        self._refreshing = False

        self.setWindowTitle(
            "YouTube Queue"
        )

        self.resize(
            680,
            520,
        )

        self.setMinimumSize(
            520,
            380,
        )

        # -------------------------------------------------
        # Add URL
        # -------------------------------------------------

        self.url_input = QLineEdit()

        self.url_input.setPlaceholderText(
            "https://www.youtube.com/watch?v=..."
        )

        self.add_button = QPushButton(
            "Add"
        )

        add_layout = QHBoxLayout()

        add_layout.addWidget(
            self.url_input
        )

        add_layout.addWidget(
            self.add_button
        )

        # -------------------------------------------------
        # Now playing
        # -------------------------------------------------

        self.now_playing_title = QLabel(
            "Now Playing"
        )

        self.now_playing_label = QLabel(
            "Nothing playing"
        )

        self.now_playing_label.setWordWrap(
            True
        )

        self.now_playing_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        # -------------------------------------------------
        # Queue
        # -------------------------------------------------

        self.queue_title = QLabel(
            "Up Next"
        )

        self.queue_list = QListWidget()

        self.queue_list.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        # Allow drag/drop reordering.
        self.queue_list.setDragDropMode(
            QAbstractItemView.InternalMove
        )

        self.queue_list.setDefaultDropAction(
            Qt.MoveAction
        )

        # -------------------------------------------------
        # Queue controls
        # -------------------------------------------------

        self.remove_button = QPushButton(
            "Remove Selected"
        )

        self.clear_button = QPushButton(
            "Clear Queue"
        )

        self.resume_button = QPushButton(
            "Play / Resume"
        )

        button_layout = QHBoxLayout()

        button_layout.addWidget(
            self.resume_button
        )

        button_layout.addStretch()

        button_layout.addWidget(
            self.remove_button
        )

        button_layout.addWidget(
            self.clear_button
        )

        # -------------------------------------------------
        # Hint
        # -------------------------------------------------

        self.hint_label = QLabel(
            "Drag items to reorder them. "
            "Double-click an item to open it on YouTube."
        )

        self.hint_label.setWordWrap(
            True
        )

        # -------------------------------------------------
        # Main layout
        # -------------------------------------------------

        layout = QVBoxLayout(
            self
        )

        layout.addLayout(
            add_layout
        )

        layout.addSpacing(
            8
        )

        layout.addWidget(
            self.now_playing_title
        )

        layout.addWidget(
            self.now_playing_label
        )

        layout.addSpacing(
            12
        )

        layout.addWidget(
            self.queue_title
        )

        layout.addWidget(
            self.queue_list
        )

        layout.addWidget(
            self.hint_label
        )

        layout.addLayout(
            button_layout
        )

        # -------------------------------------------------
        # Signals
        # -------------------------------------------------

        self.add_button.clicked.connect(
            self.add_url
        )

        self.url_input.returnPressed.connect(
            self.add_url
        )

        self.remove_button.clicked.connect(
            self.remove_selected
        )

        self.clear_button.clicked.connect(
            self.clear_queue
        )

        self.resume_button.clicked.connect(
            self.resume_queue
        )

        self.queue_list.itemDoubleClicked.connect(
            self.open_item
        )

        # rowsMoved fires after drag/drop ordering changes.
        self.queue_list.model().rowsMoved.connect(
            self.queue_reordered
        )

        # -------------------------------------------------
        # Refresh timer
        # -------------------------------------------------

        self.timer = QTimer(
            self
        )

        self.timer.timeout.connect(
            self.refresh_queue
        )

        self.timer.start(
            500
        )

        self.refresh_queue()

    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------

    def _guild_id(self):
        return self.guild_id_provider()

    # -------------------------------------------------
    # Add
    # -------------------------------------------------

    def add_url(self):
        guild_id = self._guild_id()

        if guild_id is None:
            QMessageBox.warning(
                self,
                "YouTube Queue",
                "Select a Discord server first.",
            )

            return

        url = (
            self.url_input.text()
            .strip()
        )

        if not url:
            return

        if not (
            url.startswith(
                "https://www.youtube.com/"
            )
            or url.startswith(
                "https://youtube.com/"
            )
            or url.startswith(
                "https://youtu.be/"
            )
            or url.startswith(
                "http://www.youtube.com/"
            )
            or url.startswith(
                "http://youtu.be/"
            )
        ):
            QMessageBox.warning(
                self,
                "YouTube Queue",
                (
                    "That does not look like "
                    "a YouTube URL."
                ),
            )

            return

        options = (
            self.options_provider()
            or {}
        )

        self.discord.enqueue_youtube(
            guild_id,
            url,
            volume=options.get(
                "volume",
                1.0,
            ),
            loop=False,
            start_time=None,
            stop_time=None,
            cookies_file=options.get(
                "cookies_file"
            ),
        )

        self.url_input.clear()

        self.refresh_queue()

    # -------------------------------------------------
    # Remove
    # -------------------------------------------------

    def remove_selected(self):
        guild_id = self._guild_id()

        if guild_id is None:
            return

        item = (
            self.queue_list.currentItem()
        )

        if item is None:
            return

        queue_id = item.data(
            Qt.UserRole
        )

        if queue_id is None:
            return

        self.discord.remove_youtube_queue_items(
            guild_id,
            [queue_id],
        )

        self.refresh_queue()

    # -------------------------------------------------
    # Clear
    # -------------------------------------------------

    def clear_queue(self):
        guild_id = self._guild_id()

        if guild_id is None:
            return

        if self.queue_list.count() == 0:
            return

        result = QMessageBox.question(
            self,
            "Clear YouTube Queue",
            (
                "Remove every upcoming "
                "YouTube item from the queue?"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if result != QMessageBox.Yes:
            return

        self.discord.clear_youtube_queue(
            guild_id
        )

        self.refresh_queue()

    # -------------------------------------------------
    # Resume
    # -------------------------------------------------

    def resume_queue(self):
        guild_id = self._guild_id()

        if guild_id is None:
            return

        self.discord.resume_youtube_queue(
            guild_id
        )

        self.refresh_queue()

    # -------------------------------------------------
    # Open link
    # -------------------------------------------------

    def open_item(
        self,
        item,
    ):
        url = item.data(
            Qt.UserRole + 1
        )

        if not url:
            return

        webbrowser.open(
            url
        )

    # -------------------------------------------------
    # Reorder
    # -------------------------------------------------

    def queue_reordered(self):
        if self._refreshing:
            return

        guild_id = self._guild_id()

        if guild_id is None:
            return

        queue_ids = []

        for index in range(
            self.queue_list.count()
        ):
            item = (
                self.queue_list.item(
                    index
                )
            )

            queue_id = item.data(
                Qt.UserRole
            )

            if queue_id is not None:
                queue_ids.append(
                    queue_id
                )

        self.discord.set_youtube_queue_order(
            guild_id,
            queue_ids,
        )

    # -------------------------------------------------
    # Refresh
    # -------------------------------------------------

    def refresh_queue(self):
        guild_id = self._guild_id()

        if guild_id is None:
            self.now_playing_label.setText(
                "Select a Discord server."
            )

            self._refreshing = True

            try:
                self.queue_list.clear()

            finally:
                self._refreshing = False

            return

        snapshot = (
            self.discord
            .get_youtube_queue_snapshot(
                guild_id
            )
        )

        current = snapshot.get(
            "current"
        )

        if current:
            current_url = (
                current.get("url")
                or "Unknown"
            )

            self.now_playing_label.setText(
                current_url
            )

        else:
            self.now_playing_label.setText(
                "Nothing playing"
            )

        queued = snapshot.get(
            "queue",
            [],
        )

        current_ids = []

        for index in range(
            self.queue_list.count()
        ):
            item = (
                self.queue_list.item(
                    index
                )
            )

            current_ids.append(
                item.data(
                    Qt.UserRole
                )
            )

        desired_ids = [
            entry["id"]
            for entry in queued
        ]

        # Avoid rebuilding the widget every 500 ms.
        # This is important while the user is dragging.
        if current_ids == desired_ids:
            return

        self._refreshing = True

        try:
            self.queue_list.clear()

            for position, entry in enumerate(
                queued,
                start=1,
            ):
                url = entry.get(
                    "url",
                    ""
                )

                item = QListWidgetItem(
                    f"{position}. {url}"
                )

                item.setData(
                    Qt.UserRole,
                    entry["id"],
                )

                item.setData(
                    Qt.UserRole + 1,
                    url,
                )

                item.setToolTip(
                    url
                )

                self.queue_list.addItem(
                    item
                )

        finally:
            self._refreshing = False