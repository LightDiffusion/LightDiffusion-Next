<div align="center">

# Say hi to LightDiffusion-Next 👋


**LightDiffusion-Next**  is the fastest AI-powered image generation GUI/CLI, combining speed, precision, and flexibility in one cohesive tool. 
</br>
</br>
  <a href="https://github.com/LightDiffusion/LightDiffusion-Next">
    <img src="./HomeImage.png" alt="Logo">

  </a>
</br>
</div>


As a refactored and improved version of the original [LightDiffusion repository](https://github.com/Aatrick/LightDiffusion), this project enhances usability, maintainability, and functionality while introducing a host of new features to streamline your creative workflows.  

## Motivation:

**LightDiffusion** was originally meant to be made in Rust, but due to the lack of support for the Rust language in the AI community, it was made in Python with the goal of being the simplest and fastest AI image generation tool. 

That's when the first version of LightDiffusion was born which only counted [3000 lines of code](https://github.com/LightDiffusion/LightDiffusion-original), only using Pytorch. With time, the [project](https://github.com/Aatrick/LightDiffusion) grew and became more complex, and the need for a refactor was evident. This is where **LightDiffusion-Next** comes in, with a more modular and maintainable codebase, and a plethora of new features and optimizations.

📚 Learn more in the [official documentation](https://aatrick.github.io/LightDiffusion/).  

---

## 🌟 Highlights  

**LightDiffusion-Next** offers a powerful suite of tools to cater to creators at every level. At its core, it supports **Text-to-Image** (Txt2Img) and **Image-to-Image** (Img2Img) generation, offering a variety of upscale methods and samplers, to make it easier to create stunning images with minimal effort.

Advanced users can take advantage of features like **attention syntax**, **Hires-Fix** or **ADetailer**. These tools provide better quality and flexibility for generating complex and high-resolution outputs.

**LightDiffusion-Next** is fine-tuned for **performance**. Features such as **Xformers** acceleration, **BFloat16** precision support, WaveSpeed attention block cache, and **Stable-Fast** model compilation (which offers up to a 70% speed boost) ensure smooth and efficient operation, even on demanding workloads.

---

## ✨ Feature Showcase  

Here’s what makes LightDiffusion-Next stand out:  

- **Speed and Efficiency**:  
  Enjoy industry-leading performance with built-in Xformers, Pytorch, Wavespeed and Stable-Fast optimizations, achieving up to 30% faster speeds compared to the rest of the AI image generation backends in SD1.5 and up to 2x for Flux.

- **Automatic Detailing**:  
  Effortlessly enhance faces and body details with AI-driven tools based on the [Impact Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack).  

- **State Preservation**:  
  Save and resume your progress with saved states, ensuring seamless transitions between sessions.  

- **Advanced GUI and CLI**:  
  Work through a user-friendly graphical interface or leverage the streamlined pipeline for CLI-based workflows.  

- **Integration-Ready**:  
  Collaborate and create directly in Discord with [Boubou](https://github.com/Aatrick/Boubou), or preview images dynamically with the optional **TAESD preview mode**.  

- **Image Previewing**:  
  Get a real-time preview of your generated images with TAESD, allowing for user-friendly and interactive workflows.

- **Image Upscaling**:  
  Enhance your images with advanced upscaling options like UltimateSDUpscaling, ensuring high-quality results every time.

- **Prompt Refinement**:
    Use the Llama 3.2-powered automatic prompt enhancer to refine your prompts and generate more accurate and detailed outputs.

- **LoRa and Textual Inversion Embeddings**:
    Leverage LoRa and textual inversion embeddings for highly customized and nuanced results, adding a new dimension to your creative process.

- **Low-End Device Support**:
    Run LightDiffusion-Next on low-end devices with as little as 2GB of VRAM or even no GPU, ensuring accessibility for all users.

---

## ⚡ Performance Benchmarks  

**LightDiffusion-Next** dominates in performance:  

| **Tool**                           | **Speed (it/s)** |  
|------------------------------------|------------------|  
| **LightDiffusion with Stable-Fast** | 9.2              |  
| **LightDiffusion**                 | 7.8              |  
| **ComfyUI**                        | 7.1              |  
| **SDWebUI**                        | 6.6              |  

With its unmatched speed and efficiency, LightDiffusion-Next sets the benchmark for AI image generation tools.  

---

## 🛠 Installation  

### Quick Start  

1. Download a release or clone this repository.  
2. Run `run.bat` in a terminal.  
3. Start creating!  

### Command-Line Pipeline  

For a GUI-free experience, use the pipeline:  
```bash  
pipeline.bat <prompt> <width> <height> <num_images> <batch_size>
```  
Use `pipeline.bat -h` for more options.  

---

### Advanced Setup  

- **Install from Source**:  
  Install dependencies via:  
  ```bash  
  pip install -r requirements.txt  
  ```  
  Add your SD1/1.5 safetensors model to the `checkpoints` directory, then launch the application.  

- **⚡Stable-Fast Optimization**:  
  Follow [this guide](https://github.com/chengzeyi/stable-fast?tab=readme-ov-file#installation) to enable Stable-Fast mode for optimal performance.  

- **🦙 Prompt Enhancer**:  
  Refine your prompts with Llama 3.2:  
  ```bash  
  pip install ollama  
  ollama run llama3.1  
  ```  
  See the [Ollama guide](https://github.com/ollama/ollama?tab=readme-ov-file) for details.  

- **🤖 Discord Integration**:  
  Set up the Discord bot by following the [Boubou installation guide](https://github.com/Aatrick/Boubou).  

---

🎨 Enjoy exploring the powerful features of LightDiffusion-Next!  
