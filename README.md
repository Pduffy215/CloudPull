Stream Puller

Pulls posted vibration survey documents from ARCA and reconstructs them into local .bin/.wav files for a selected site and survey.

Run it: python rawStreamPuller.py

Flow: pick a site/survey in a GUI (already-pulled surveys are marked, unposted ones are excluded) → a background thread (PullWorker) downloads each document for that survey from ARCA, decodes the waveform data, and writes out per-bearing folders with a live progress bar → once done (or cancelled), you're back at the picker to pull another survey.

Files:

rawStreamPuller.py — entry point, wires everything together
PullWorker.py — does the actual pulling and file-writing work, off the GUI thread
StreamPullerGUI.py — site/survey picker (site_picker_GUI)
LoadingBarPullGUI.py — progress bar, with cancel support
Config.py — paths, API keys, URLs