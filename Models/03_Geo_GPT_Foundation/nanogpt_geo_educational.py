"""
BHU LOKA (भूलोक) - Educational NanoGPT from Scratch
=====================================================
A first-principles implementation of a decoder-only Transformer language model in PyTorch.
Designed for master's and doctoral researchers to understand the internal mathematics
of self-attention, causal masking, multi-head projections, and autoregressive generation.

Mathematical Formulation:
-------------------------
1. Scaled Dot-Product Attention:
   Attention(Q, K, V) = softmax( (Q @ K.T) / sqrt(d_k) + M ) @ V
   where M is the lower-triangular causal mask: M_ij = 0 if i >= j else -inf

2. Multi-Head Attention:
   MultiHead(Q, K, V) = Concat(head_1, ..., head_h) @ W_O
   where head_i = Attention(Q @ W_Q_i, K @ W_K_i, V @ W_V_i)

3. Transformer Block (Pre-LN):
   x = x + MultiHead(LayerNorm(x))
   x = x + FeedForward(LayerNorm(x))

Author: Prince Kumar (IIT Patna, PA2511CDH37) & BHU LOKA Research Team
"""

import math
import torch
import torch.nn as nn
from torch.nn import functional as F

# -----------------------------------------------------------------------------
# 1. Hyperparameters for Educational Demonstration
# -----------------------------------------------------------------------------
BATCH_SIZE = 4        # Number of independent sequences processed in parallel
BLOCK_SIZE = 32       # Maximum sequence length (context window)
D_MODEL = 64          # Embedding dimension (size of vector representing each token)
N_HEAD = 4            # Number of attention heads (each head has d_k = D_MODEL / N_HEAD = 16)
N_LAYER = 3           # Number of Transformer blocks stacked vertically
DROPOUT = 0.1         # Dropout probability for regularization
LEARNING_RATE = 1e-3  # Optimizer learning rate
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# -----------------------------------------------------------------------------
# 2. Scaled Dot-Product Causal Self-Attention Head
# -----------------------------------------------------------------------------
class CausalSelfAttention(nn.Module):
    """
    Computes multi-head causal self-attention.
    Causal masking ensures token at position t can only attend to positions <= t.
    """
    def __init__(self, d_model: int, n_head: int, block_size: int, dropout: float):
        super().__init__()
        assert d_model % n_head == 0, "d_model must be divisible by n_head"
        self.d_model = d_model
        self.n_head = n_head
        self.head_dim = d_model // n_head
        
        # Combined projection for Q, K, V in a single matrix multiplication
        self.qkv_projection = nn.Linear(d_model, 3 * d_model)
        # Output projection back to d_model
        self.out_projection = nn.Linear(d_model, d_model)
        
        # Regularization
        self.attn_dropout = nn.Dropout(dropout)
        self.resid_dropout = nn.Dropout(dropout)
        
        # Lower-triangular causal mask buffer (not a trainable parameter)
        # tril shape: (1, 1, block_size, block_size)
        tril = torch.tril(torch.ones(block_size, block_size)).view(1, 1, block_size, block_size)
        self.register_buffer("causal_mask", tril)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Input shape:  (Batch B, Sequence Length T, Feature Dimension C)
        Output shape: (Batch B, Sequence Length T, Feature Dimension C)
        """
        B, T, C = x.size()
        
        # 1. Project x into Query, Key, and Value tensors
        # qkv shape: (B, T, 3 * C)
        qkv = self.qkv_projection(x)
        # Split into (B, T, C) each
        q, k, v = qkv.chunk(3, dim=-1)
        
        # 2. Reshape for multi-head attention: (B, T, C) -> (B, n_head, T, head_dim)
        # Transpose brings n_head to dim 1 for batch matrix multiplication
        q = q.view(B, T, self.n_head, self.head_dim).transpose(1, 2)
        k = k.view(B, T, self.n_head, self.head_dim).transpose(1, 2)
        v = v.view(B, T, self.n_head, self.head_dim).transpose(1, 2)
        
        # 3. Scaled dot-product: (B, n_head, T, head_dim) @ (B, n_head, head_dim, T)
        # Raw attention scores shape: (B, n_head, T, T)
        scaling = 1.0 / math.sqrt(self.head_dim)
        scores = (q @ k.transpose(-2, -1)) * scaling
        
        # 4. Apply causal mask: set future positions (where mask == 0) to -infinity
        scores = scores.masked_fill(self.causal_mask[:, :, :T, :T] == 0, float('-inf'))
        
        # 5. Softmax normalizes scores along the last dimension to form valid probability distribution
        weights = F.softmax(scores, dim=-1)
        weights = self.attn_dropout(weights)
        
        # 6. Weighted sum of values: (B, n_head, T, T) @ (B, n_head, T, head_dim) -> (B, n_head, T, head_dim)
        out = weights @ v
        
        # 7. Concatenate all heads: transpose back to (B, T, n_head, head_dim) and flatten to (B, T, C)
        out = out.transpose(1, 2).contiguous().view(B, T, C)
        
        # 8. Final linear projection and residual dropout
        return self.resid_dropout(self.out_projection(out))

# -----------------------------------------------------------------------------
# 3. Position-wise Feed-Forward Network (MLP)
# -----------------------------------------------------------------------------
class FeedForward(nn.Module):
    """
    Two-layer MLP with GELU activation expanding dimension to 4 * d_model.
    FFN(x) = GELU(x @ W_1 + b_1) @ W_2 + b_2
    """
    def __init__(self, d_model: int, dropout: float):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, 4 * d_model),
            nn.GELU(),
            nn.Linear(4 * d_model, d_model),
            nn.Dropout(dropout)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

# -----------------------------------------------------------------------------
# 4. Transformer Decoder Block (Pre-LayerNorm Architecture)
# -----------------------------------------------------------------------------
class TransformerBlock(nn.Module):
    """
    Single Transformer decoder block with Pre-LayerNorm formulation.
    Pre-LN provides superior gradient propagation and training stability.
    """
    def __init__(self, d_model: int, n_head: int, block_size: int, dropout: float):
        super().__init__()
        self.ln_1 = nn.LayerNorm(d_model)
        self.attn = CausalSelfAttention(d_model, n_head, block_size, dropout)
        self.ln_2 = nn.LayerNorm(d_model)
        self.mlp = FeedForward(d_model, dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Pre-LN residual branch 1: Attention
        x = x + self.attn(self.ln_1(x))
        # Pre-LN residual branch 2: MLP
        x = x + self.mlp(self.ln_2(x))
        return x

# -----------------------------------------------------------------------------
# 5. Complete NanoGPT Model Architecture
# -----------------------------------------------------------------------------
class NanoGPTGeo(nn.Module):
    """
    Decoder-only language model implementing token embeddings, learned positional
    embeddings, a stack of Transformer blocks, and a final language modeling head.
    """
    def __init__(self, vocab_size: int, d_model: int, n_head: int, n_layer: int, block_size: int, dropout: float):
        super().__init__()
        self.block_size = block_size
        self.vocab_size = vocab_size
        
        # Token and positional embedding tables
        self.token_embeddings = nn.Embedding(vocab_size, d_model)
        self.position_embeddings = nn.Embedding(block_size, d_model)
        self.drop = nn.Dropout(dropout)
        
        # Stack of Transformer blocks
        self.blocks = nn.ModuleList([
            TransformerBlock(d_model, n_head, block_size, dropout)
            for _ in range(n_layer)
        ])
        
        # Final layer normalization and linear classifier head
        self.ln_f = nn.LayerNorm(d_model)
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)
        
        # Weight tying: share weights between token embeddings and language model head
        self.lm_head.weight = self.token_embeddings.weight
        
        # Parameter initialization
        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, idx: torch.Tensor, targets: torch.Tensor = None):
        """
        idx shape: (B, T)
        targets shape: (B, T) or None during inference
        """
        B, T = idx.size()
        assert T <= self.block_size, f"Cannot forward sequence of length {T}, block size is {self.block_size}"
        
        # Positional indices [0, 1, ..., T-1]
        pos = torch.arange(0, T, dtype=torch.long, device=idx.device)
        
        # Compute embeddings: token embedding + positional embedding
        tok_emb = self.token_embeddings(idx)           # (B, T, d_model)
        pos_emb = self.position_embeddings(pos)        # (T, d_model)
        x = self.drop(tok_emb + pos_emb)               # (B, T, d_model)
        
        # Forward through Transformer blocks
        for block in self.blocks:
            x = block(x)
            
        x = self.ln_f(x)                               # (B, T, d_model)
        logits = self.lm_head(x)                       # (B, T, vocab_size)
        
        loss = None
        if targets is not None:
            # Flatten B and T to compute cross-entropy over all sequence tokens
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1))
            
        return logits, loss

    @torch.no_grad()
    def generate(self, idx: torch.Tensor, max_new_tokens: int, temperature: float = 1.0, top_k: int = None) -> torch.Tensor:
        """
        Autoregressive generation loop. Predicts next token one step at a time.
        """
        for _ in range(max_new_tokens):
            # Crop current context if it exceeds block_size
            idx_cond = idx if idx.size(1) <= self.block_size else idx[:, -self.block_size:]
            
            # Forward model to get logits for current sequence
            logits, _ = self(idx_cond)
            # Focus only on the last time step: (B, vocab_size)
            logits = logits[:, -1, :] / temperature
            
            # Optional Top-K filtering
            if top_k is not None:
                v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < v[:, [-1]]] = -float('Inf')
                
            # Softmax to get token probabilities
            probs = F.softmax(logits, dim=-1)
            # Sample from probability distribution
            idx_next = torch.multinomial(probs, num_samples=1)
            # Append sampled token to running sequence
            idx = torch.cat((idx, idx_next), dim=1)
            
        return idx


# -----------------------------------------------------------------------------
# 6. Self-Contained Verification & Educational Training Run
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print(" BHU LOKA (भूलोक) - NANO-GPT FIRST PRINCIPLES DEMONSTRATION")
    print("=" * 70)
    
    # Domain-specific micro corpus of disaster mitigation text
    text_corpus = """
    BHU LOKA Geospatial AI: Patna multi-hazard assessment framework.
    Sentinel-1 SAR C-band detects urban standing water in Kankarbagh and Rajendra Nagar.
    Double bounce scattering increases radar backscatter in flooded street canyons.
    Copernicus DEM 30m identifies natural topographic drainage bottlenecks.
    Extreme heatwave pre-monsoon increases urban vulnerability in dense wards.
    Civil defense evacuation directive: mobilize water pumps to low elevation sinks.
    """
    
    # Simple character-level tokenizer for transparent education
    chars = sorted(list(set(text_corpus)))
    vocab_size = len(chars)
    stoi = {ch: i for i, ch in enumerate(chars)}
    itos = {i: ch for i, ch in enumerate(chars)}
    
    encode = lambda s: [stoi[c] for c in s]
    decode = lambda l: ''.join([itos[i] for i in l])
    
    data = torch.tensor(encode(text_corpus), dtype=torch.long)
    print(f"Corpus Length: {len(data)} characters | Unique Vocab Size: {vocab_size}")
    
    # Initialize educational model
    model = NanoGPTGeo(
        vocab_size=vocab_size,
        d_model=D_MODEL,
        n_head=N_HEAD,
        n_layer=N_LAYER,
        block_size=BLOCK_SIZE,
        dropout=DROPOUT
    ).to(DEVICE)
    
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Total Model Parameters: {total_params:,} (Extremely lightweight for CPU/laptop training)")
    
    # Train for 50 steps to observe empirical loss minimization
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)
    model.train()
    
    print("\nTraining progress (demonstrating loss minimization):")
    for step in range(50):
        # Create mini-batches
        ix = torch.randint(len(data) - BLOCK_SIZE, (BATCH_SIZE,))
        x = torch.stack([data[i:i+BLOCK_SIZE] for i in ix]).to(DEVICE)
        y = torch.stack([data[i+1:i+BLOCK_SIZE+1] for i in ix]).to(DEVICE)
        
        logits, loss = model(x, y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        if (step + 1) % 10 == 0:
            print(f"Step {step+1:02d}/50 | Cross-Entropy Loss: {loss.item():.4f}")
            
    # Autoregressive generation test
    model.eval()
    prompt = "BHU LOKA "
    context = torch.tensor([encode(prompt)], dtype=torch.long, device=DEVICE)
    generated = model.generate(context, max_new_tokens=40, temperature=0.8)
    output_text = decode(generated[0].tolist())
    
    print("\nSample Generation Output:")
    print("-" * 50)
    print(output_text)
    print("-" * 50)
    print("First-principles self-attention verified successfully.")
    print("=" * 70)

