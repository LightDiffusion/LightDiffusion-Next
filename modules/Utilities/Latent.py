import torch
from modules.Device import Device


class LatentFormat:
    """#### Base class for latent formats.
    
    #### Attributes:
        - `scale_factor` (float): The scale factor for the latent format.

    #### Returns:
        - `LatentFormat`: A latent format object.
    """
    scale_factor = 1.0

    def process_in(self, latent):
        """#### Process the latent input, by multiplying it by the scale factor.

        #### Args:
            - `latent` (torch.Tensor): The latent tensor.

        #### Returns:
            - `torch.Tensor`: The processed latent tensor.
        """
        return latent * self.scale_factor

    def process_out(self, latent):
        """#### Process the latent output, by dividing it by the scale factor.
        
        #### Args:
            - `latent` (torch.Tensor): The latent tensor.
            
        #### Returns:
            - `torch.Tensor`: The processed latent tensor.
        """
        return latent / self.scale_factor


class SD15(LatentFormat):
    """#### SD15 latent format.

    #### Args:
        - `LatentFormat` (LatentFormat): The base latent format class.
    """
    def __init__(self, scale_factor=0.18215):
        self.scale_factor = scale_factor
        self.latent_rgb_factors = [
            #   R        G        B
            [0.3512, 0.2297, 0.3227],
            [0.3250, 0.4974, 0.2350],
            [-0.2829, 0.1762, 0.2721],
            [-0.2120, -0.2616, -0.7177],
        ]
        self.taesd_decoder_name = "taesd_decoder"
        
class EmptyLatentImage:
    def __init__(self):
        self.device = Device.intermediate_device()

    def generate(self, width, height, batch_size=1):
        latent = torch.zeros(
            [batch_size, 4, height // 8, width // 8], device=self.device
        )
        return ({"samples": latent},)