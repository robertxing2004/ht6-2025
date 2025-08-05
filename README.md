# ht6-2025

## Demo Video
[![Watch the video](https://img.youtube.com/vi/UbA8Ath_Yyg/maxresdefault.jpg)](https://youtu.be/UbA8Ath_Yyg?feature=shared)


## Inspiration
Inspired by the high demand for battery energy storage to support the adoption of renewable energy sources, we planned to tackle a rising issue of refurbishing lithium-ion EV batteries for static applications in order to maximize humanity's usage of this highly limited but invaluable resource.

## What it does
Our project acts as a proof of concept for an embedded system that aims to aid reliability, safety, and future proofing of second-life batteries (SLBs). As SLBs are still a relatively new technology faced with various logistical issues, our system acts as a an out-of-the-box battery management system (BMS) designed to integrate batteries with varying specifications and allow them to work seamlessly together. The BMS also feeds its telemetry to a centralized dashboard, allowing system administrators to monitor the status of their SLB fleets on the fly.

## How we built it
Since we obviously don't have real battery packs to test, we first used PyBamm to create a continuous telemetry feed from a simulated battery module. For our demo, we are simulating an array of three EV batteries, each containing 6912 individual cells, with various degraded characteristics to emulate the degraded performance of used car batteries.

Since we don't have a physical connection between battery module and edge device, our QNX-powered Raspberry Pi receives this telemetry feed via TCP in binary format, emulating how the physical connections on BMSs receive data in operation.

The edge device then does some local monitoring on its own and can also trigger failsafes if certain operational limits are exceeded. This is to simulate how the BMS would react to anomalies if it were physically connected to the battery module by temporarily shutting down batteries or other physical measures in response to issues such as overheating, overcurrent, etc.
We wanted to leverage the RTOS' low resource costs and guaranteed reliability to ensure the stability of the system.

The edge device also sends data to a FastAPI server, allowing users to view live telemetry on a web dashboard. In our current implementation, this data is sent via API requests, which we recognize is not an ideal setup. This is because we were unable to get a robust socket connection established between the Pi and the server. 
The data is stored on a MongoDB Atlas cluster, and we have leveraged the Gemini API to provide live insights, visualizations, and battery health predictions, providing insights into all SLBs' potential performance and cost savings. 
