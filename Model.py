import torch
import torch.nn as nn
class Demucs(nn.Module):
    def __init__(self, audio_channels=1):
        super(Demucs, self).__init__()
        self.encoder = nn.Sequential(
            nn.Conv1d(audio_channels, 64, kernel_size=8, stride=4, padding=2),
            nn.ReLU(),
            nn.Conv1d(64, 128, kernel_size=8, stride=4, padding=2),
            nn.ReLU(),
            nn.Conv1d(128, 256, kernel_size=8, stride=4, padding=2),
            nn.ReLU(),
        )

        self.lstm = nn.LSTM(input_size=256, hidden_size=512, num_layers=2, batch_first=True, bidirectional=True)

        self.decoder = nn.Sequential(
            nn.ConvTranspose1d(1024, 128, kernel_size=8, stride=4, padding=2),
            nn.ReLU(),
            nn.ConvTranspose1d(128, 64, kernel_size=8, stride=4, padding=2),
            nn.ReLU(),
            nn.ConvTranspose1d(64, audio_channels, kernel_size=8, stride=4, padding=2),
        )
    def forward(self, x):
        x = self.encoder(x)
        x = x.permute(0, 2, 1)  # (batch, seq, features) for LSTM
        x, _ = self.lstm(x)
        x = x.permute(0, 2, 1)  # back to (batch, features, seq)
        x = self.decoder(x)
        return x