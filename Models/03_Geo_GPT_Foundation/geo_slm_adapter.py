"""
BHU LOKA (भूलोक) - Multi-Modal Geospatial Language Model Adapter
==================================================================
Architectural bridge connecting multi-band Earth Observation features
(Sentinel-1 SAR, Copernicus DEM, MODIS LST, WorldPop) to a compact Language Model.

Scientific Architecture:
------------------------
1. Spatial Feature Vector (or Raster Patch):
   z_spatial in R^(B x D_in), where D_in = [SAR_pre, SAR_post, Delta_sigma0, Elev, Slope, TWI, LST, Pop]
2. Projection MLP (Adapter):
   z_tokens = MLP(z_spatial) in R^(B x K x D_llm)
   Transforms physical geospatial features into virtual prompt tokens.
3. Language Model Embedding Fusion:
   Fused_Input = [Virtual_Geo_Tokens; Text_Instruction_Tokens]
4. Autoregressive Decision-Support Generation:
   Predicts structured multi-hazard vulnerability and civil defense directives.

Author: Prince Kumar (IIT Patna, PA2511CDH37) & BHU LOKA Research Team
"""

import torch
import torch.nn as nn
from typing import Dict, Any

class GeospatialFeatureProjector(nn.Module):
    """
    Projects raw physical geospatial measurements into LLM token embeddings.
    """
    def __init__(self, in_features: int = 8, num_virtual_tokens: int = 4, d_llm: int = 2048):
        super().__init__()
        self.num_virtual_tokens = num_virtual_tokens
        self.d_llm = d_llm
        
        # 2-layer MLP projection network with GELU non-linearity
        self.projector = nn.Sequential(
            nn.Linear(in_features, 256),
            nn.LayerNorm(256),
            nn.GELU(),
            nn.Linear(256, num_virtual_tokens * d_llm),
            nn.Dropout(0.1)
        )
        
    def forward(self, geo_features: torch.Tensor) -> torch.Tensor:
        """
        Input:  (B, in_features)
        Output: (B, num_virtual_tokens, d_llm)
        """
        B = geo_features.size(0)
        projected = self.projector(geo_features)
        # Reshape to (Batch, Virtual Tokens, LLM Hidden Dimension)
        return projected.view(B, self.num_virtual_tokens, self.d_llm)

class BhuLokaGeoSLM(nn.Module):
    """
    Complete Multi-Modal Decision Support Model Architecture.
    Combines Spatial Feature Projector with an LLM token space.
    """
    def __init__(self, in_features: int = 8, num_virtual_tokens: int = 4, d_llm: int = 256):
        super().__init__()
        self.projector = GeospatialFeatureProjector(
            in_features=in_features,
            num_virtual_tokens=num_virtual_tokens,
            d_llm=d_llm
        )
        # Prediction head for calibrated multi-hazard risk probability
        self.risk_head = nn.Sequential(
            nn.Linear(d_llm * num_virtual_tokens, 128),
            nn.ReLU(),
            nn.Linear(128, 3) # [Flood Risk, Heat Stress Risk, Combined Vulnerability]
        )
        
    def forward(self, geo_features: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Computes virtual tokens for LLM conditioning and direct risk probabilities.
        """
        virtual_tokens = self.projector(geo_features) # (B, K, d_llm)
        flattened = virtual_tokens.view(virtual_tokens.size(0), -1)
        risk_logits = self.risk_head(flattened)
        risk_probs = torch.sigmoid(risk_logits)
        
        return {
            "virtual_tokens": virtual_tokens,
            "risk_probabilities": risk_probs
        }

if __name__ == "__main__":
    print("=" * 70)
    print(" BHU LOKA (भूलोक) - MULTI-MODAL GEOSPATIAL ADAPTER TEST")
    print("=" * 70)
    
    # Example batch of 2 locations in Patna:
    # Location 1: Rajendra Nagar (Low elevation, dense built-up, urban double bounce SAR)
    # Location 2: Danapur Cantt (Higher elevation, lower waterlogging, moderate population)
    # Feature columns: [SAR_pre_dB, SAR_post_dB, Delta_sigma0, Elev_m, Slope_deg, TWI, LST_degC, Pop_count]
    sample_features = torch.tensor([
        [-12.4, -9.8, +2.6, 44.5, 0.4, 11.2, 42.1, 14200.0],  # Rajendra Nagar
        [-11.8, -12.1, -0.3, 52.1, 1.8, 6.8, 38.5, 4100.0]    # Danapur Cantt
    ], dtype=torch.float32)
    
    model = BhuLokaGeoSLM(in_features=8, num_virtual_tokens=4, d_llm=128)
    output = model(sample_features)
    
    print(f"Input Geospatial Tensor Shape : {sample_features.shape}")
    print(f"Virtual Tokens Tensor Shape   : {output['virtual_tokens'].shape}")
    print(f"Risk Probabilities Shape      : {output['risk_probabilities'].shape}")
    print("\nPredicted Calibrated Risk Scores [Flood, Heat, Combined]:")
    print(f"  Rajendra Nagar : {output['risk_probabilities'][0].detach().numpy().round(3)}")
    print(f"  Danapur Cantt  : {output['risk_probabilities'][1].detach().numpy().round(3)}")
    print("=" * 70)

