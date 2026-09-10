// Prints Mesen struct sizes/offsets used by mesen_probe.py. Build from a MesenCE checkout:
//   clang++ -std=c++17 -I. -ICore -IUtilities -o layout mesen_layout_check.cpp && ./layout
#include "pch.h"
#include "Shared/SettingTypes.h"
#include "SNES/SnesCpuTypes.h"
#include "Debugger/DebugTypes.h"
#include "Debugger/ITraceLogger.h"
#include <cstdio>
#include <cstddef>
int main(){
  printf("KeyMapping %zu KeyMappingSet %zu ControllerConfig %zu SnesConfig %zu\n", sizeof(KeyMapping), sizeof(KeyMappingSet), sizeof(ControllerConfig), sizeof(SnesConfig));
  printf("off Region %zu AllowInvalidInput %zu ColorCorrection %zu HideBgLayer1 %zu Overscan %zu InterpolationType %zu ChannelVolumes %zu EnableRandomPowerOnState %zu RamPowerOnState %zu SpcClockSpeedAdjustment %zu BsxCustomDate %zu\n",
    offsetof(SnesConfig,Region), offsetof(SnesConfig,AllowInvalidInput), offsetof(SnesConfig,ColorCorrection), offsetof(SnesConfig,HideBgLayer1), offsetof(SnesConfig,Overscan), offsetof(SnesConfig,InterpolationType), offsetof(SnesConfig,ChannelVolumes), offsetof(SnesConfig,EnableRandomPowerOnState), offsetof(SnesConfig,RamPowerOnState), offsetof(SnesConfig,SpcClockSpeedAdjustment), offsetof(SnesConfig,BsxCustomDate));
  printf("EmulationConfig %zu SnesCpuState %zu off A %zu PC %zu K %zu PS %zu\n", sizeof(EmulationConfig), sizeof(SnesCpuState), offsetof(SnesCpuState,A), offsetof(SnesCpuState,PC), offsetof(SnesCpuState,K), offsetof(SnesCpuState,PS));
  printf("DebugControllerState %zu TraceLoggerOptions %zu TraceRow %zu\n", sizeof(DebugControllerState), sizeof(TraceLoggerOptions), sizeof(TraceRow));
  return 0; }
