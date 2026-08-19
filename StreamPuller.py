from StreamPullerGUI import site_picker_GUI, reselect
from LoadingBarPullGUI import LoadingBar
from SplashScreenFunctions import SplashFunctions
from PullWorker import PullWorker
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

def get_arca_documents():
    app = QApplication.instance() or QApplication([])  # reuse existing app instance if one exists

    splash = SplashFunctions()
    splash.show()
    splash.start_fade_in()
    app.exec_()  # blocks until splash screen closes itself

    result = site_picker_GUI()  # let user pick a survey/site to pull
    if result is None:
        print("No site selected — exiting.\n")
        return
    measurement_start_time, data, dialog = result  # dialog stays open for potential reselection later

    while True:  # loop lets the user reselect and retry after a cancel
        print("\nStream Puller Starting")

        worker = PullWorker(measurement_start_time, data)  # background thread that does the actual pulling
        bar = LoadingBar(1)  # progress bar, total gets updated once real doc count is known
        cancelled = False
        pending_errors = []  # collects the errors

        def on_progress(count, total, prefix):
            if bar.total != total:
                bar.set_total(total)  # update total once actual document count comes in
            bar.update(count, prefix)

        def on_finished():
            app.quit()  # exit the nested event loop, let the outer code continue

        def on_failed(message):
            print(message)
            bar._done = True
            bar.close()
            app.quit()  # exit the nested event loop on failure too

        def on_cancel_requested():
            nonlocal cancelled
            cancelled = True
            bar.label.setText("Cancelling...")
            worker.requestInterruption()  # ask the worker thread to stop at its next check

        def on_error(title, msg):
            pending_errors.append((title, msg))  # queued but not shown anywhere yet

        def on_update_speed(speed, min_speed, max_speed):
            if bar is not None:
                bar.update_speed(speed, min_speed, max_speed)  # live Mbps readout

        # wire up worker/bar signals, all queued so they run safely on the GUI thread
        worker.progress.connect(on_progress, Qt.QueuedConnection)
        worker.finished_ok.connect(on_finished, Qt.QueuedConnection)
        worker.failed.connect(on_failed, Qt.QueuedConnection)
        worker.error_occurred.connect(on_error, Qt.QueuedConnection)
        bar.cancelled.connect(on_cancel_requested, Qt.QueuedConnection)
        worker.update_speed.connect(on_update_speed, Qt.QueuedConnection)

        worker.start()  # start the background pull
        app.exec_()      # block here until finished/failed/cancelled quits this nested loop
        worker.wait()    # make sure the old thread is fully done before reusing app.exec_

        for title, msg in pending_errors:
            QMessageBox.critical(None, title, msg)  # show each per-item error as a popup
        pending_errors.clear()

        if not cancelled:
            print("\nStream Puller Finished Succesfully\n")
            dialog.close()
            break  # normal completion, exit the retry loop

        picked = reselect(dialog)  # cancelled — offer the user a chance to pick again
        if picked is None:
            dialog.close()
            break  # user gave up on reselecting, exit entirely
        measurement_start_time, data = picked  # loop back around and retry the pull

if __name__ == "__main__":
    get_arca_documents()