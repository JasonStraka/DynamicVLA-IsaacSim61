"""CPU-only API boundary checks; no simulator or GPU initialization."""
import ast
from pathlib import Path
import unittest
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
NAMES = {'config_quat_from_wxyz', 'quat_wxyz_to_isaac', 'quat_isaac_to_wxyz',
         'pose_action_wxyz_to_isaac', 'pose_action_isaac_to_wxyz',
         'as_torch', 'as_numpy', 'config_quaternions_to_wxyz'}

def boundaries(xyzw):
    tree = ast.parse((ROOT / 'simulations/helpers.py').read_text(encoding='utf-8'))
    selected = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in NAMES], type_ignores=[])
    ns = {'np': np, 'torch': torch, '_ISAAC_USES_XYZW': xyzw}
    exec(compile(selected, 'helpers-boundaries', 'exec'), ns)
    return ns

class CompatibilityTests(unittest.TestCase):
    def test_sources_parse(self):
        for path in ROOT.rglob('*.py'):
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))

    def test_quaternion_roundtrip(self):
        h = boundaries(True)
        q = torch.tensor([[1., 2., 3., 4.]])
        self.assertEqual(h['quat_wxyz_to_isaac'](q).tolist(), [[2., 3., 4., 1.]])
        self.assertTrue(torch.equal(h['quat_isaac_to_wxyz'](h['quat_wxyz_to_isaac'](q)), q))

    def test_action_boundary(self):
        h = boundaries(True)
        a = torch.arange(16.).reshape(2, 8)
        original = a.clone()
        converted = h['pose_action_wxyz_to_isaac'](a)
        self.assertTrue(torch.equal(a, original))
        self.assertTrue(torch.equal(converted[:, :3], a[:, :3]))
        self.assertTrue(torch.equal(converted[:, 7:], a[:, 7:]))
        self.assertTrue(torch.equal(h['pose_action_isaac_to_wxyz'](converted), a))

    def test_old_api_noop(self):
        h = boundaries(False)
        q = (1., 0., 0., 0.)
        self.assertIs(h['config_quat_from_wxyz'](q), q)
        a = torch.zeros(2, 8)
        self.assertIs(h['pose_action_wxyz_to_isaac'](a), a)

    def test_config_roundtrip(self):
        h = boundaries(True)
        for q in [(1., 2., 3., 4.), [1., 2., 3., 4.], np.array([1., 2., 3., 4.])]:
            result = h['config_quat_from_wxyz'](q)
            self.assertEqual(type(result), type(q))
            self.assertEqual(h['config_quaternions_to_wxyz']({'robot': {'rot': result}})['robot']['rot'], [1., 2., 3., 4.])

    def test_proxy_materialization(self):
        h = boundaries(True)
        class Proxy:
            def torch(self):
                return torch.tensor([[2., 3., 4., 1.]])
        self.assertEqual(h['as_torch'](Proxy(), quaternion=True).tolist(), [[1., 2., 3., 4.]])
        self.assertIsInstance(h['as_numpy'](Proxy()), np.ndarray)

    def test_protocol_tensor_not_double_converted(self):
        h = boundaries(True)
        q = torch.tensor([[1., 2., 3., 4.]])
        self.assertIs(h['as_torch'](q, quaternion=True), q)

    def test_startup_order(self):
        s = (ROOT / 'simulations/evaluate.py').read_text(encoding='utf-8')
        self.assertLess(s.index('isaaclab_args.enable_cameras = True'), s.index('app_launcher = AppLauncher'))
        self.assertLess(s.index('app_launcher = AppLauncher'), s.index('import gymnasium'))

if __name__ == '__main__':
    unittest.main()
