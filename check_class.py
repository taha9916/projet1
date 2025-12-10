try:
    from transformers import AutoModelForVision2Seq
    print('La classe AutoModelForVision2Seq existe')
except ImportError:
    print('La classe AutoModelForVision2Seq n\'existe pas')

try:
    from transformers import SmolVLMForConditionalGeneration
    print('La classe SmolVLMForConditionalGeneration existe')
except ImportError:
    print('La classe SmolVLMForConditionalGeneration n\'existe pas')