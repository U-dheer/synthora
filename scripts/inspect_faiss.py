#!/usr/bin/env python3
"""
inspect_faiss.py

Load a FAISS index file, extract IDs and vectors (where possible), and export
all data (ids, vectors, metadata sidecars) into CSV/NPY/JSON.

Usage examples:
  python scripts/inspect_faiss.py /path/to/index.file --export-csv out.csv
  python scripts/inspect_faiss.py /path/to/index.file --export-npy vectors.npy
  python scripts/inspect_faiss.py /path/to/index.file --export-json all.json

Dependencies:
  pip install faiss-cpu numpy pandas
  (or `faiss-gpu` instead of `faiss-cpu` if you have GPU + CUDA)
"""

import argparse
import os
import sys
import json
import pickle
from typing import Optional, List

try:
    import faiss
except Exception as e:
    print("Error importing faiss:", e)
    print("Install with: pip install faiss-cpu numpy pandas")
    sys.exit(1)

import numpy as np

try:
    import pandas as pd
except Exception:
    pd = None


def find_sidecars(index_path: str) -> List[str]:
    base = os.path.splitext(index_path)[0]
    candidates = []
    for ext in ('.pkl', '.json', '.npy', '.db', '.sqlite', '.csv'):
        p = base + ext
        if os.path.exists(p):
            candidates.append(p)
    d = os.path.dirname(index_path) or '.'
    for f in os.listdir(d):
        if os.path.splitext(f)[0].startswith(os.path.splitext(os.path.basename(index_path))[0]) and f != os.path.basename(index_path):
            candidates.append(os.path.join(d, f))
    return sorted(set(candidates))


def try_extract_id_map(index) -> Optional[np.ndarray]:
    # IndexIDMap often wraps an index and has an `id_map` field accessible via faiss.vector_to_array
    try:
        if 'IndexIDMap' in index.__class__.__name__:
            try:
                ids = faiss.vector_to_array(index.id_map)
                return np.array(ids, dtype=np.int64)
            except Exception:
                # sometimes id_map is attribute already a list/ndarray
                ids = getattr(index, 'id_map', None)
                if ids is not None:
                    return np.array(ids, dtype=np.int64)
    except Exception:
        pass
    return None


def load_sidecar(path: str):
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif ext == '.pkl':
            with open(path, 'rb') as f:
                return pickle.load(f)
        elif ext == '.npy':
            return np.load(path, allow_pickle=True)
        elif ext in ('.csv', '.db', '.sqlite'):
            return path  # return path for user to inspect (too big to auto-parse sometimes)
    except Exception as e:
        return f'ERROR_LOADING: {e}'
    return None


def inspect_index(path: str, export_csv: Optional[str], export_npy: Optional[str], export_json: Optional[str], limit: Optional[int]):
    print(f'Reading index: {path}')
    index = faiss.read_index(path)

    print('Index class:', index.__class__.__name__)
    try:
        print('dimension (d):', index.d)
    except Exception:
        pass
    try:
        print('ntotal:', index.ntotal)
    except Exception:
        pass
    try:
        print('is_trained:', index.is_trained)
    except Exception:
        pass

    id_map = try_extract_id_map(index)
    if id_map is not None:
        print('Detected IndexIDMap with', len(id_map), 'external ids')
    else:
        print('No IndexIDMap detected (or extraction failed) — internal ids will be used')

    try:
        nt = int(index.ntotal)
    except Exception:
        nt = None

    to_process = nt if (limit is None and nt is not None) else min(limit or nt or 0, nt or (limit or 0))

    print('Will attempt to reconstruct', to_process, 'vectors (this may take time).')

    ids_out = []
    vectors_out = []
    failures = 0

    if to_process and to_process > 0:
        for i in range(to_process):
            try:
                vec = index.reconstruct(i)
                arr = np.array(vec, dtype=float).reshape(-1)
                vectors_out.append(arr)
                if id_map is not None and i < len(id_map):
                    ids_out.append(int(id_map[i]))
                else:
                    ids_out.append(i)
            except Exception as e:
                failures += 1
                vectors_out.append(None)
                ids_out.append(None)
                print(f'  reconstruct({i}) failed: {e}')

    # If we couldn't reconstruct any vectors but have nt, optionally attempt a range search for each id
    if (len([v for v in vectors_out if v is not None]) == 0) and nt and nt > 0:
        print('No vectors reconstructed. The index might be a quantized or GPU-only type. You can try converting on the machine that created it or use specialized FAISS helpers.')

    # Prepare export
    metadata = {}
    sidecars = find_sidecars(path)
    if sidecars:
        print('Found sidecar files:')
        for s in sidecars:
            print(' ', s)
            metadata[os.path.basename(s)] = load_sidecar(s)
    else:
        print('No sidecar files found nearby.')

    # Export CSV
    if export_csv:
        if pd is None:
            print('Pandas not installed — cannot export CSV. Install with `pip install pandas`')
        else:
            rows = []
            good_vectors = []
            for idx, vec in zip(ids_out, vectors_out):
                if vec is not None:
                    rows.append({'id': idx, **{f'f{i}': float(x) for i, x in enumerate(vec)}})
                    good_vectors.append(vec)
            if len(rows) == 0:
                print('No vectors to write to CSV.')
            else:
                df = pd.DataFrame(rows)
                df.to_csv(export_csv, index=False)
                print('Wrote CSV to', export_csv)

    # Export NPY (just the vectors matrix)
    if export_npy:
        good = [v for v in vectors_out if v is not None]
        if len(good) == 0:
            print('No vectors to write to NPY.')
        else:
            arr = np.vstack(good)
            np.save(export_npy, arr)
            print('Wrote NPY to', export_npy)

    # Export combined JSON (ids + vectors + sidecars) — vectors serialized as lists
    if export_json:
        out = {
            'index_path': path,
            'index_class': index.__class__.__name__,
            'ntotal': nt,
            'ids': ids_out,
            'vectors': [v.tolist() if v is not None else None for v in vectors_out],
            'sidecars': metadata,
        }
        with open(export_json, 'w', encoding='utf-8') as f:
            json.dump(out, f)
        print('Wrote JSON to', export_json)

    print('\nSummary:')
    print('  attempted:', to_process)
    print('  reconstructed:', len([v for v in vectors_out if v is not None]))
    print('  failures:', failures)
    print('Done.')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('index', help='Path to FAISS index file')
    p.add_argument('--limit', '-n', type=int, default=None, help='Max vectors to attempt to reconstruct (default: all)')
    p.add_argument('--export-csv', help='Export reconstructed vectors and ids to CSV')
    p.add_argument('--export-npy', help='Export reconstructed vectors to NPY')
    p.add_argument('--export-json', help='Export ids + vectors + sidecars into a single JSON')
    args = p.parse_args()

    inspect_index(args.index, args.export_csv, args.export_npy, args.export_json, args.limit)


if __name__ == '__main__':
    main()
