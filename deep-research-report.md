# System Requirements  
First, check your Windows and hardware. AMD’s HIP/ROCm SDK for Windows requires **Windows 11 (64-bit) version 22H2 or later**. (Windows 10 is not supported by the latest SDK.) You also need a modern CPU that supports PCIe atomics – essentially **AMD Zen (2nd gen or newer) or Intel Haswell and later**.  

Next, check your GPU/APU. ROCm on Windows only works with AMD graphics. Supported cards include **RDNA3-series GPUs** (e.g. Radeon RX 7900/7800/7700/7600 series) and **RDNA2 GPUs** (e.g. RX 6900/6800 series). New AMD "Ryzen AI" APUs (RDNA3.5) like the **Ryzen AI Max** models are also supported. (If your GPU is not on AMD’s supported list – for example, Nvidia or an older Radeon – the SDK will not work.) Your GPU drivers must be up-to-date: the HIP SDK installer will include AMD’s Radeon Software (PRO Edition) driver version 25.30. You should also update your current AMD Adrenalin/PRO driver to the latest version before installing. 

# Prerequisite Steps  
- **Windows Update**: Fully update Windows 11 to 22H2 (Settings > Windows Update). If you’re on Windows 10, consider upgrading or use a supported machine.  
- **Driver Cleanup**: If you have existing AMD GPU drivers, use the HIP installer’s **Factory Reset** option or the AMD Cleanup Utility to remove them first. This avoids conflicts.  
- **User Privileges**: You need an Administrator account to install the SDK and drivers.  
- **Development Tools (optional)**: Install Visual Studio 2017/2019/2022 if you plan to use the HIP VS plugin or compile HIP code. (Not strictly required for basic setup.)  

# Installation Steps  
1. **Download the AMD HIP SDK**: Go to AMD’s ROCm developer site and find the HIP SDK download page for Windows. Choose the version matching your needs (for Windows 11, use HIP SDK 7.1.1). Click the Windows installer link (you will need to accept AMD’s license). Save the `.exe` file.  
2. **Run the Installer**: Right-click the downloaded installer and select “Run as administrator”. When prompted, allow the **Factory Reset** to remove old drivers (if it asks). Follow the GUI: the installer will auto-detect your system and select the appropriate components. By default it installs the full HIP SDK **and** the bundled AMD Radeon Software PRO driver.  
3. **Customize (Optional)**: You can de-select any components you don’t need, but it’s easiest to keep the defaults. Make sure the GPU driver component is selected so your AMD graphics driver gets installed.  
4. **Install and Reboot**: Click “Install” and wait. The installer may show progress windows. Once finished, the AMD driver install will require a **system restart**. Restart your PC to complete the installation.  
5. **Post-Install Setup**: After reboot, open **System Properties → Environment Variables** and add the ROCm `bin` folder to your PATH. For example, add  
   ```
   C:\Program Files\AMD\ROCm\7.1\bin
   ```  
   (Use the actual version number installed.) Alternatively, open a new PowerShell/Command window and run:  
   ```powershell
   $env:PATH += ';C:\Program Files\AMD\ROCm\7.1\bin'
   ```  
   This ensures Windows can find the HIP tools.  

# Verification  
Once installed, verify that HIP sees your GPU. In a new terminal, run `hipInfo` or `hipconfig`. You should see output listing your AMD GPU and HIP version. For example, it should report your GPU name and PCI bus info. If `hipInfo` runs without errors and shows your device, the install was successful.  

# Known Issues and Tips  
- **Driver Versions**: The installer uses Radeon Software PRO 25.30, which is stable for ROCm. Ensure your existing system is up-to-date with AMD’s latest drivers (Adrenalin Edition 2023 or PRO drivers) before installing. As one user notes, “ensure you have [a] recent Adrenaline driver and install this ROCm SDK”.  
- **Headless Systems**: The Windows HIP installer needs a user session (it has a GUI entry point), so make sure you’re running it interactively (no headless/no-console mode).  
- **GPU Support**: If your GPU is on the supported list above, you should be good. If `hipInfo` shows no device, double-check that your GPU model appears in AMD’s support table. Unsupported cards will not be recognized.  
- **Uninstalling**: If you need to remove ROCm later, use “Add/Remove Programs” in Windows Settings to uninstall each AMD HIP SDK component.  

# Summary  
In short, **yes** – if your PC meets the requirements above, you can install the AMD ROCm/HIP SDK on Windows now (before using any cloud credits). This setup will let you test AMD acceleration locally on your Ryzen AI or Radeon GPU. The official docs make it clear what’s needed – Windows 11 (22H2), a supported AMD GPU/CPU, and the HIP SDK installer which includes the GPU driver. Once installed and verified (via `hipInfo`), you’ll be ready to run AMD-based inference without waiting for the cloud resources.  

**Sources:** Official AMD ROCm/HIP SDK Windows documentation, which detail OS/GPU requirements and installation steps.