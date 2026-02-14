import hashlib
import threading

import numpy as np

from igor2.binarywave import load as loadibw
from igor2.packed import load as loadpxp

from helper import data_dir


def tostr(data):
    if isinstance(data, bytes):
        data = data.decode("utf-8")
    return data


def _array_fingerprint(data):
    # Array signature for equality checks
    array = np.ascontiguousarray(data)
    return (
        str(array.dtype),
        tuple(int(i) for i in array.shape),
        hashlib.sha256(array.tobytes()).hexdigest(),
    )


def _ibw_fingerprint(path):
    data = loadibw(path)
    wave = data["wave"]["wData"]
    header = data["wave"]["wave_header"]
    # Include metadata plus payload signature for equality checks.
    return (
        int(data["version"]),
        tostr(header["bname"]),
        _array_fingerprint(wave),
    )


def _pxp_fingerprint(path, initial_byte_order):
    records, filesystem = loadpxp(path, initial_byte_order=initial_byte_order)
    # Check both tree shape and wave payloads for equality checks.
    root_keys = tuple(sorted(tostr(key) for key in filesystem["root"].keys()))
    waves = []
    for record in records:
        if hasattr(record, "wave"):
            wave = record.wave["wave"]["wData"]
            name = tostr(record.wave["wave"]["wave_header"]["bname"])
            waves.append((name,) + _array_fingerprint(wave))
    return (len(records), root_keys, tuple(waves))


def _run_concurrent_workload(worker_count, iterations_per_worker, task):
    barrier = threading.Barrier(worker_count)
    errors = []
    lock = threading.Lock()

    def worker(thread_id):
        try:
            barrier.wait()
            for iteration in range(iterations_per_worker):
                task(thread_id, iteration)
        except Exception as exc:
            with lock:
                errors.append(f"thread {thread_id}: {exc!r}")

    threads = []
    for thread_id in range(worker_count):
        thread = threading.Thread(target=worker, args=(thread_id,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    assert not errors, "\n".join(errors[:10])


def test_pxp():
    data = loadpxp(data_dir / 'polar-graphs-demo.pxp')
    records = data[0]
    assert len(records) == 51

    assert records[30].variables == {'version': 1,
                                     'variables': {
                                         'var_header': {'numSysVars': 21,
                                                        'numUserVars': 0,
                                                        'numUserStrs': 0},
                                         'sysVars': {'K0': 0.0,
                                                     'K1': 0.0,
                                                     'K2': 0.0,
                                                     'K3': 0.0,
                                                     'K4': 0.0,
                                                     'K5': 0.0,
                                                     'K6': 0.0,
                                                     'K7': 0.0,
                                                     'K8': 0.0,
                                                     'K9': 0.0,
                                                     'K10': 0.0,
                                                     'K11': 0.0,
                                                     'K12': 0.0,
                                                     'K13': 0.0,
                                                     'K14': 0.0,
                                                     'K15': 0.0,
                                                     'K16': 0.0,
                                                     'K17': 0.0,
                                                     'K18': 0.0,
                                                     'K19': 0.0,
                                                     'K20': 128.0},
                                         'userVars': {},
                                         'userStrs': {}}}

    wave = data[1]["root"]
    wkeys = [tostr(st) for st in wave.keys()]
    assert sorted(wkeys) == sorted(
        ['K0', 'K1', 'K2', 'K3', 'K4', 'K5', 'K6', 'K7', 'K8', 'K9', 'K10',
         'K11', 'K12', 'K13', 'K14', 'K15', 'K16', 'K17', 'K18', 'K19', 'K20',
         'radiusData', 'angleData', 'W_plrX5', 'W_plrY5', 'angleQ1',
         'radiusQ1', 'W_plrX6', 'W_plrY6', 'Packages']
    )

    assert np.allclose(records[32].wave["wave"]["wData"], np.array(
        [0.3, 0.5448544, 0.77480197, 0.9758435, 1.1357394, 1.2447554,
         1.2962544, 1.287101, 1.2178528, 1.0927255, 0.91933674,
         0.7082426, 0.47229454, 0.22585714, -0.01606643,
         -0.23874778, -0.42862982, -0.574153, -0.6664573, -0.6999235,
         -0.6725141, -0.5858976, -0.44534767, -0.25942117, -0.03943586,
         0.20121357, 0.44787762, 0.6855388, 0.8997279, 1.0774051,
         1.2077546, 1.2828392, 1.2980883, 1.2525737, 1.1490659,
         0.99386656, 0.7964253, 0.5687607, 0.32473388, 0.07920124,
         -0.15288824, -0.35740662, -0.5219018, -0.636359, -0.69381076,
         -0.69075894, -0.62739, -0.5075599, -0.3385666, -0.13069656,
         0.10339352, 0.34945396, 0.5925036, 0.8177455, 1.0114669,
         1.1618733, 1.2598093, 1.2993116, 1.277976, 1.1971004,
         1.061609, 0.8797508, 0.6625979, 0.4233691, 0.17663053,
         -0.06259823, -0.2797519, -0.46160996, -0.597101, -0.6779761,
         -0.6993116, -0.6598092, -0.56187314, -0.41146588, -0.21774435,
         0.00749773, 0.25054744, 0.49660596, 0.7306987, 0.9385669,
         1.1075606, 1.2273898, 1.2907591, 1.2938106, 1.2363585,
         1.1219027, 0.95740634, 0.7528879, 0.5207975, 0.2752648,
         0.03123802, -0.19642642, -0.39386547, -0.54906607, -0.6525743,
         -0.6980884, -0.682839, -0.607754, -0.47740453, -0.29972947,
         -0.08553842, 0.15212469, 0.39878684, 0.6394367, 0.85942155,
         1.0453486, 1.1858985, 1.2725141, 1.2999234, 1.2664578,
         1.1741526, 1.0286293, 0.83874667, 0.6160649, 0.37414294,
         0.12770344, -0.1082412, -0.3193372, -0.49272597, -0.6178533,
         -0.6871013, -0.6962544, -0.6447547, -0.5357403, -0.37584305,
         -0.17479956, 0.05514668, 0.30000135],
        dtype=np.float32))

    assert np.allclose(records[33].wave["wave"]["wData"], np.array([
        0., 0.0494739, 0.0989478, 0.1484217, 0.1978956,
        0.24736951, 0.29684341, 0.34631732, 0.3957912, 0.44526511,
        0.49473903, 0.54421294, 0.59368682, 0.6431607, 0.69263464,
        0.74210852, 0.79158241, 0.84105635, 0.89053023, 0.94000411,
        0.98947805, 1.03895199, 1.08842587, 1.13789964, 1.18737364,
        1.23684752, 1.2863214, 1.3357954, 1.38526928, 1.43474305,
        1.48421705, 1.53369093, 1.58316481, 1.63263881, 1.68211269,
        1.73158658, 1.78106046, 1.83053434, 1.88000822, 1.92948222,
        1.9789561, 2.02842999, 2.07790399, 2.12737775, 2.17685175,
        2.22632551, 2.27579927, 2.32527351, 2.37474728, 2.42422128,
        2.47369504, 2.52316904, 2.5726428, 2.6221168, 2.67159081,
        2.72106457, 2.77053857, 2.82001233, 2.86948609, 2.91896009,
        2.9684341, 3.0179081, 3.06738186, 3.11685586, 3.16632962,
        3.21580338, 3.26527762, 3.31475139, 3.36422539, 3.41369915,
        3.46317315, 3.51264691, 3.56212091, 3.61159492, 3.66106868,
        3.71054268, 3.76001644, 3.8094902, 3.85896444, 3.90843821,
        3.95791221, 4.00738621, 4.05685997, 4.10633373, 4.15580797,
        4.20528126, 4.2547555, 4.30422926, 4.3537035, 4.40317726,
        4.45265102, 4.50212526, 4.55159855, 4.60107279, 4.65054703,
        4.70002079, 4.74949455, 4.79896832, 4.84844255, 4.89791584,
        4.94739008, 4.99686432, 5.04633808, 5.09581184, 5.14528561,
        5.19475985, 5.24423361, 5.29370737, 5.34318161, 5.3926549,
        5.44212914, 5.4916029, 5.54107714, 5.5905509, 5.64002466,
        5.6894989, 5.73897219, 5.78844643, 5.83792019, 5.88739443,
        5.93686819, 5.98634195, 6.03581619, 6.08528948, 6.13476372,
        6.18423796, 6.23371172, 6.28318548], dtype=np.float32))

    assert np.allclose(records[39].wave["wave"]["wData"], np.array([
        8.19404411, 8.88563347, 9.70543861, 10.17177773,
        10.11173058, 9.73756695, 9.25513077, 8.8788929,
        9.16085339, 10.56489944, 12.75579453, 14.90572262,
        16.46352959, 17.33401871, 17.68511391, 17.74635315,
        17.70048141, 17.79942513, 18.36241531, 19.38741684,
        20.41767311, 21.02259827, 21.09260368, 20.4905529,
        18.95538521, 16.9299469, 15.94969368, 17.14490509,
        19.78741264, 22.33615875, 23.96352196, 24.04369545,
        21.92454147, 18.79150391, 17.77407646, 20.32803917,
        24.37140465, 27.24079132, 28.40307808, 28.67787933,
        28.70550728, 28.50283432, 27.68538666, 26.36607552,
        25.73583984, 26.78374672, 28.8236084, 30.36226463,
        30.91939545, 31.22146797, 31.97431755, 32.95656204,
        33.4611969, 33.23248672, 32.3250885, 30.64473915,
        28.72983551, 28.05199242, 29.29024887, 31.3501091,
        32.7331543, 32.87995529, 32.28799438, 31.99738503],
        dtype=np.float32))


def test_pxt():
    data = loadpxp(data_dir / 'packed-byteorder.pxt', initial_byte_order='>')
    records = data[0]
    assert len(records) == 2
    assert records[0].variables == {'version': 2,
                                    'variables': {
                                        'var_header': {'numSysVars': 0,
                                                       'numUserVars': 0,
                                                       'numUserStrs': 0,
                                                       'numDependentVars': 0,
                                                       'numDependentStrs': 0},
                                        'sysVars': {},
                                        'userVars': {},
                                        'userStrs': {},
                                        'dependentVars': [],
                                        'dependentStrs': []}}
    assert np.allclose(records[1].wave['wave']["wData"][:30, 0], np.array(
        [14603., 13701., 14907., 13795., 14339., 14942., 14984., 14261.,
         12647., 14242., 14470., 13913., 14158., 14754., 14462., 14346.,
         14219., 13467., 13595., 14331., 13960., 12934., 12897., 13557.,
         13105., 12797., 13234., 13053., 13455., 12825.], dtype='>f8'))


def test_thread_safe():
    jobs = [
        (data_dir / "polar-graphs-demo.pxp", None),
        (data_dir / "packed-byteorder.pxt", ">"),
    ]
    expected = {job: _pxp_fingerprint(*job) for job in jobs}

    def task(thread_id, iteration):
        job = jobs[(thread_id + iteration) % len(jobs)]
        assert _pxp_fingerprint(*job) == expected[job]

    _run_concurrent_workload(
        worker_count=32,
        iterations_per_worker=12,
        task=task,
    )


def test_thread_safe_mixed():
    ibw_jobs = [
        data_dir / "mac-double.ibw",
        data_dir / "win-double.ibw",
        data_dir / "mac-version5.ibw",
        data_dir / "win-version5.ibw",
    ]
    pxp_jobs = [
        (data_dir / "polar-graphs-demo.pxp", None),
        (data_dir / "packed-byteorder.pxt", ">"),
    ]

    expected_ibw = {job: _ibw_fingerprint(job) for job in ibw_jobs}
    expected_pxp = {job: _pxp_fingerprint(*job) for job in pxp_jobs}
    all_jobs = (
        [("ibw", job) for job in ibw_jobs] + [("pxp", job) for job in pxp_jobs]
    )

    def task(thread_id, iteration):
        kind, payload = all_jobs[(thread_id * 3 + iteration) % len(all_jobs)]
        if kind == "ibw":
            assert _ibw_fingerprint(payload) == expected_ibw[payload]
        else:
            assert _pxp_fingerprint(*payload) == expected_pxp[payload]

    _run_concurrent_workload(
        worker_count=32,
        iterations_per_worker=10,
        task=task,
    )
