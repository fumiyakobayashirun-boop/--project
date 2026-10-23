import sys, torch, torch.nn as nn, torch.nn.functional as F
class SRVGGNetCompact(nn.Module):
    def __init__(self, num_feat=64, num_conv=32, upscale=4):
        super().__init__()
        self.upscale = upscale
        self.body = nn.ModuleList([nn.Conv2d(3, num_feat, 3, 1, 1), nn.PReLU(num_parameters=num_feat)])
        for _ in range(num_conv):
            self.body.append(nn.Conv2d(num_feat, num_feat, 3, 1, 1))
            self.body.append(nn.PReLU(num_parameters=num_feat))
        self.body.append(nn.Conv2d(num_feat, 3 * upscale * upscale, 3, 1, 1))
        self.upsampler = nn.PixelShuffle(upscale)
    def forward(self, x):
        out = x
        for layer in self.body:
            out = layer(out)
        out = self.upsampler(out)
        return out + F.interpolate(x, scale_factor=self.upscale, mode="nearest")
m = SRVGGNetCompact()
sd = torch.load(sys.argv[1], map_location="cpu")
m.load_state_dict(sd.get("params_ema", sd.get("params", sd)))
m.eval()
x = torch.rand(1, 3, 64, 64)
torch.onnx.export(m, x, sys.argv[2], input_names=["input"], output_names=["output"],
    dynamic_axes={"input": {2: "h", 3: "w"}, "output": {2: "h4", 3: "w4"}}, opset_version=17, dynamo=False)
import onnxruntime as ort, numpy as np
s = ort.InferenceSession(sys.argv[2])
y = s.run(None, {"input": x.numpy()})[0]
print("max diff", np.abs(y - m(x).detach().numpy()).max(), y.shape)
