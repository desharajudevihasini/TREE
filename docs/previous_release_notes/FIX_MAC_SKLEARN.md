# Mac test failure: `No module named _loss`

The trained NEED model was saved with **scikit-learn 1.8.0**. Earlier project requirements allowed versions 1.4–1.9, so some Mac installs selected 1.9.1. scikit-learn does not guarantee backward/forward compatibility for pickle/joblib models.

## If you already extracted the old release

In a **second Terminal** (leave the Uvicorn server running in its first Terminal):

```bash
cd ~/Downloads/TREE_Rubric_Release
source .venv311/bin/activate
python -m pip install 'scikit-learn==1.8.0'
python -m pytest -q
```

If you're working in `TREE_Rubric_Release 2`, use `cd "$HOME/Downloads/TREE_Rubric_Release 2"` instead.

## If you downloaded this fixed release

Extract `TREE_Rubric_Fixed.zip`, then:

```bash
cd ~/Downloads/TREE_Rubric_Fixed
bash start_mac.sh
```

This version pins `scikit-learn==1.8.0` in requirements and checks the installed version at startup.

Testing in a **second Terminal**:

```bash
cd ~/Downloads/TREE_Rubric_Fixed
source .venv311/bin/activate
python -m pytest -q
```

Note: changing packages while the old Uvicorn server is already running does not restart that process. Stop and restart it after the installation if the real-UK prediction API is being used.
