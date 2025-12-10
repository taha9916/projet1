#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Patch pour le modèle dots.ocr qui contourne la dépendance à flash_attn.

Ce module applique un patch au modèle dots.ocr pour qu'il puisse fonctionner
sans la bibliothèque flash_attn, qui nécessite CUDA.
"""

import logging
import sys
import types
from typing import Optional, Dict, Any, Union

# Configuration du logging
logger = logging.getLogger(__name__)

def apply_patches():
    """
    Applique les patches nécessaires pour contourner la dépendance à flash_attn.
    
    Cette fonction doit être appelée avant de charger le modèle dots.ocr.
    """
    logger.info("Application des patches pour contourner la dépendance à flash_attn")
    
    # Créer un faux module flash_attn
    flash_attn_module = types.ModuleType('flash_attn')
    flash_attn_module.__spec__ = types.SimpleNamespace(name='flash_attn')
    sys.modules['flash_attn'] = flash_attn_module
    
    # Créer une fausse fonction flash_attn_func qui utilise l'attention standard de PyTorch
    def mock_flash_attn_func(q, k, v, dropout_p=0.0, softmax_scale=None, causal=False):
        import torch
        import torch.nn.functional as F
        
        # Implémentation simplifiée de l'attention qui utilise l'API standard de PyTorch
        bsz, num_heads, seq_len, head_dim = q.shape
        q = q / (head_dim ** 0.5 if softmax_scale is None else softmax_scale)
        
        # Calculer les scores d'attention
        attn_weights = torch.matmul(q, k.transpose(-2, -1))
        
        # Appliquer le masque causal si nécessaire
        if causal:
            causal_mask = torch.triu(torch.ones(seq_len, seq_len, device=q.device), diagonal=1).bool()
            attn_weights.masked_fill_(causal_mask.unsqueeze(0).unsqueeze(0), float('-inf'))
        
        # Appliquer softmax
        attn_weights = F.softmax(attn_weights, dim=-1)
        
        # Appliquer dropout si nécessaire
        if dropout_p > 0.0:
            attn_weights = F.dropout(attn_weights, p=dropout_p)
        
        # Calculer la sortie
        attn_output = torch.matmul(attn_weights, v)
        
        return attn_output
    
    # Ajouter la fonction mock au module flash_attn
    sys.modules['flash_attn'].flash_attn_func = mock_flash_attn_func
    
    # Créer un faux module flash_attn_interface
    flash_attn_interface_module = types.ModuleType('flash_attn.flash_attn_interface')
    flash_attn_interface_module.__spec__ = types.SimpleNamespace(name='flash_attn.flash_attn_interface')
    flash_attn_interface_module.flash_attn_func = mock_flash_attn_func
    sys.modules['flash_attn.flash_attn_interface'] = flash_attn_interface_module
    
    logger.info("Patches appliqués avec succès")

# Appliquer les patches automatiquement lors de l'importation du module
apply_patches()