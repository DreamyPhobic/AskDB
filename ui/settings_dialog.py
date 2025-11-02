from __future__ import annotations

from typing import Optional
from PySide6 import QtWidgets, QtCore

from core.config_store import SettingsManager


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, settings: SettingsManager, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.settings = settings
        self._did_initial_size = False

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # Scrollable content for small screens
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._scroll = scroll
        content = QtWidgets.QWidget()
        self._content = content
        scroll.setWidget(content)
        body = QtWidgets.QVBoxLayout(content)
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(12)

        # Provider group
        provider_box = QtWidgets.QGroupBox("Model & Provider")
        provider_form = QtWidgets.QFormLayout(provider_box)
        provider_form.setLabelAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        provider_form.setFormAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        provider_form.setHorizontalSpacing(14)
        provider_form.setVerticalSpacing(10)

        self.model_combo = QtWidgets.QComboBox()
        self.model_combo.addItems(["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-3.5-turbo"])
        self.model_combo.setEditable(True)
        self.model_combo.setCurrentText(self.settings.model_name)
        self.model_combo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self.key_edit = QtWidgets.QLineEdit()
        self.key_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.key_edit.setPlaceholderText("Enter your OPENAI_API_KEY…")
        self.key_edit.setText(self.settings.api_key)
        self.key_edit.setMinimumWidth(360)
        self.key_edit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        # Show/Hide toggle for API key
        show_api = QtWidgets.QCheckBox("Show")
        show_api.setChecked(False)
        def _toggle_api(v: int) -> None:
            self.key_edit.setEchoMode(QtWidgets.QLineEdit.Normal if show_api.isChecked() else QtWidgets.QLineEdit.Password)
        show_api.stateChanged.connect(_toggle_api)
        api_row = QtWidgets.QHBoxLayout()
        api_row.addWidget(self.key_edit, 1)
        api_row.addWidget(show_api, 0, QtCore.Qt.AlignRight)
        api_row_w = QtWidgets.QWidget()
        api_row_w.setLayout(api_row)

        provider_form.addRow("Model", self.model_combo)
        provider_form.addRow("OpenAI API Key", api_row_w)

        # Observability group
        obs_box = QtWidgets.QGroupBox("Observability (LangSmith)")
        obs_form = QtWidgets.QFormLayout(obs_box)
        obs_form.setLabelAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        obs_form.setFormAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        obs_form.setHorizontalSpacing(14)
        obs_form.setVerticalSpacing(10)

        self.tracing_check = QtWidgets.QCheckBox("Enable LangSmith tracing")
        self.tracing_check.setChecked(self.settings.enable_tracing)
        self.langsmith_key = QtWidgets.QLineEdit(self.settings.langsmith_api_key)
        self.langsmith_key.setEchoMode(QtWidgets.QLineEdit.Password)
        self.langsmith_key.setPlaceholderText("LANGCHAIN_API_KEY (optional)")
        self.langsmith_project = QtWidgets.QLineEdit(self.settings.langsmith_project)
        self.langsmith_project.setPlaceholderText("Project name (optional)")
        self.langsmith_key.setMinimumWidth(360)
        self.langsmith_project.setMinimumWidth(280)
        self.langsmith_key.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.langsmith_project.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        def _sync_tracing(enabled: bool) -> None:
            self.langsmith_key.setEnabled(enabled)
            self.langsmith_project.setEnabled(enabled)
        _sync_tracing(self.tracing_check.isChecked())
        self.tracing_check.toggled.connect(_sync_tracing)

        obs_form.addRow(self.tracing_check)
        obs_form.addRow("LangSmith API Key", self.langsmith_key)
        obs_form.addRow("LangSmith Project", self.langsmith_project)

        # Add groups to body
        body.addWidget(provider_box)
        body.addWidget(obs_box)
        body.addStretch(1)

        # Buttons pinned at bottom
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        self._btns = btns

        root.addWidget(scroll, 1)
        root.addWidget(btns, 0, QtCore.Qt.AlignRight)

        # Open at the dialog's recommended size based on its contents
        try:
            self.adjustSize()
        except Exception:
            # Fallback in rare cases where adjustSize may fail during construction
            self.resize(self.sizeHint())

    def accept(self) -> None:  # type: ignore[override]
        self.settings.data["model_name"] = self.model_combo.currentText()
        self.settings.data["openai_api_key"] = self.key_edit.text().strip()
        self.settings.data["enable_tracing"] = bool(self.tracing_check.isChecked())
        self.settings.data["langsmith_api_key"] = self.langsmith_key.text().strip()
        self.settings.data["langsmith_project"] = self.langsmith_project.text().strip()
        self.settings.save()
        super().accept()

    def showEvent(self, event: QtCore.QEvent) -> None:  # type: ignore[override]
        super().showEvent(event)
        # On first show, resize to recommended size bounded by available screen
        if not getattr(self, "_did_initial_size", False):
            try:
                # Compute desired size so that scrollbars are not needed
                content_hint = self._content.sizeHint()
                btns_hint = self._btns.sizeHint() if hasattr(self, "_btns") else QtCore.QSize(0, 0)
                # Add layout margins/padding (approximate)
                horiz_margins = 24
                vert_margins = 24 + 10  # root margins + spacing above buttons
                desired_w = content_hint.width() + horiz_margins
                desired_h = content_hint.height() + btns_hint.height() + vert_margins

                hint = QtCore.QSize(max(400, desired_w), max(300, desired_h))
                screen = QtWidgets.QApplication.primaryScreen()
                if screen is not None:
                    avail = screen.availableGeometry()
                    max_w = int(avail.width() * 0.9)
                    max_h = int(avail.height() * 0.9)
                    w = min(hint.width(), max_w)
                    h = min(hint.height(), max_h)
                    self.resize(max(400, w), max(300, h))
                else:
                    self.resize(hint)
            except Exception:
                pass
            self._did_initial_size = True


