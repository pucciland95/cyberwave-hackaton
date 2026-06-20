import os
from pathlib import Path

from cyberwave import Cyberwave


def print_twin_connection_info(twin) -> None:
    # Stampa una conferma leggibile: se questi valori escono, la lettura del
    # twin via API Cyberwave e' andata a buon fine.
    print("Cyberwave connection OK")
    print(f"mode: {cw.config.runtime_mode}")
    print(f"environment_id: {cw.config.environment_id}")
    print(f"requested_twin_id: {os.getenv('CYBERWAVE_TWIN_UUID') or 'not set'}")
    print(f"resolved_twin_uuid: {twin.uuid}")
    print(f"resolved_twin_name: {twin.name}")
    print(f"resolved_twin_class: {type(twin).__name__}")

    # Mostra solo le capability principali, utili per capire se lo SDK ha
    # riconosciuto l'UGV come robot mobile.
    capabilities = twin.capabilities
    print(f"can_locomote: {bool(capabilities.get('can_locomote'))}")
    print(f"has_wheels: {bool(capabilities.get('has_wheels'))}")

    sensors = capabilities.get("sensors", [])
    sensor_summary = ", ".join(
        f"{sensor.get('id', 'unknown')}:{sensor.get('type', 'unknown')}"
        for sensor in sensors
        if isinstance(sensor, dict)
    )
    print(f"sensors: {sensor_summary or 'none'}")


def load_local_env() -> None:
    # `tutorial.py` e' in `src/cyberwave_hackaton/locomotion/`.
    # `parents[3]` risale alla root del progetto, dove abbiamo creato `.env`.
    env_path = Path(__file__).resolve().parents[3] / ".env"

    # Se `.env` non esiste, lo script usa solo le variabili gia' presenti
    # nell'ambiente del terminale.
    if not env_path.exists():
        return

    # Legge il file `.env` riga per riga.
    for line in env_path.read_text().splitlines():
        line = line.strip()

        # Salta righe vuote, commenti e righe che non sono assegnazioni KEY=VALUE.
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)

        # Imposta la variabile solo se non e' gia' stata esportata nel terminale.
        # Questo permette di sovrascrivere `.env` temporaneamente da shell.
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


# Carica `.env` prima di creare il client Cyberwave, cosi' il client trova
# `CYBERWAVE_API_KEY`, `CYBERWAVE_ENVIRONMENT_ID`, `CYBERWAVE_TWIN_UUID`, ecc.
load_local_env()

# Crea il client Cyberwave.
# `CYBERWAVE_MODE=simulation` configura il client per la simulazione.
# Se `CYBERWAVE_MODE` non e' impostata, usa `live` come default.
cw = Cyberwave(mode=os.getenv("CYBERWAVE_MODE", "live"))

# Se abbiamo `CYBERWAVE_TWIN_UUID`, usiamo quel twin specifico gia' presente
# nell'environment. Nel nostro caso e' l'UGV Beast della scena.
twin_id = os.getenv("CYBERWAVE_TWIN_UUID")
if twin_id:
    ugv_beast = cw.twin(twin_id=twin_id)
else:
    # Altrimenti lo SDK cerca o crea un twin dell'asset `waveshare/ugv-beast`
    # nell'environment configurato.
    ugv_beast = cw.twin("waveshare/ugv-beast")

# Conferma subito quale twin e' stato letto/risolto.
print_twin_connection_info(ugv_beast)
cw.affect("sim")  # Associa il twin al client Cyberwave, necessario per la locomozione.
 
# Edit transform in the studio
# Sposta il digital twin nella scena Cyberwave Studio.
# Nota: questo NON manda un comando di movimento al robot/simulatore.
ugv_beast.edit_position(x=1, y=0, z=0.5)

# Ruota il digital twin nella scena Cyberwave Studio.
# Anche questo e' un edit visuale della scena, non una rotazione fisica.
ugv_beast.edit_rotation(yaw=90)  # degrees
 
# Joint control
# Alcuni asset hanno giunti controllabili. UGV Beast dichiara `has_joints=False`,
# quindi usiamo la capability e non `hasattr`, per evitare comandi joint inutili.
if ugv_beast.capabilities.get("has_joints"):
    ugv_beast.joints.arm_joint = 45  # degrees
 
# Locomotion
# Queste due righe pubblicano comandi MQTT di movimento.
# Le lasciamo disabilitate di default per evitare movimenti accidentali sul robot reale.
if os.getenv("UGV_RUN_DEMO_MOTION") == "1":
    # Nell'SDK Cyberwave locale `distance` qui e' una velocita' lineare in m/s,
    # non una distanza in metri. `1.0` significa quindi circa 1 m/s.
    ugv_beast.move_forward(distance=1.0)

    # `angle` qui e' una velocita' angolare in rad/s, non un angolo assoluto.
    ugv_beast.turn_left(angle=1.57)
else:
    print("motion skipped: set UGV_RUN_DEMO_MOTION=1 to run the demo movement")
 
# Start streaming sensor data
# `start_streaming()` NON legge la camera dell'UGV.
# Serve a prendere una sorgente locale/URL dal tuo PC (`camera_id=0` di default)
# e inviarla a Cyberwave. Per leggere la camera del robot usa `camera_check.py`.
if os.getenv("UGV_STREAM_LOCAL_CAMERA") == "1":
    ugv_beast.start_streaming()
else:
    print("local streaming skipped: use camera_check.py for the UGV camera")
