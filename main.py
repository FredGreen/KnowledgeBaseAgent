"""智能问答 Agent 桌面应用入口."""

import sys
import asyncio
from pathlib import Path

try:
    import qasync
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
except ImportError:
    print("PyQt6 and qasync are required. Install with:")
    print("  pip install PyQt6 qasync")
    sys.exit(1)

from src.qa_agent.app import Application
from src.qa_agent.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("智能问答 Agent")
    app.setOrganizationName("IntelligentQA")

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    application = Application()

    window = MainWindow(
        config_service=application.config_service,
        session_service=application.session_service,
        chat_service=application.chat_service,
        kb_service=application.kb_service,
    )
    window.show()

    async def _shutdown():
        await application.shutdown()

    app.aboutToQuit.connect(lambda: loop.create_task(_shutdown()))

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
