#!/usr/bin/env python3

import os
import linecache

# create .v file for simulation
# -----------------------------

if os.path.exists("gen_mem_trace.v"):
  os.remove("gen_mem_trace.v")
if os.path.exists("gen_mem_trace.s43"):
  os.remove("gen_mem_trace.s43")

f= open("gen_mem_trace.v","w+")

f.write("/*===========================================================================*/\r\n")
f.write("/*                 SANCUS MODULE DMA VIOLATION                               */\r\n")
f.write("/*---------------------------------------------------------------------------*/\r\n")
f.write("/* Test DMA violations by accessing secret SM memory from outside.           */\r\n")
f.write("/*                                                                           */\r\n")
f.write("/*---------------------------------------------------------------------------*/\r\n")
f.write("/*===========================================================================*/\r\n")
f.write("\r\n")
f.write("`define DMA_DONE_ADDR           (`DMEM_BASE+16'h60)\r\n")
f.write("`define FOO_SECRET_ADDR         (`DMEM_BASE+16'h62)\r\n")
f.write("`define FOO_SECRET              (mem262)\r\n")
f.write("`define FOO_SECRET_VAL          (16'hf00d)\r\n")
f.write("`define FOO_TEXT_ADDR           (sm_0_public_end-2)\r\n")
f.write("`define FOO_TEXT_VAL            (16'hcafe)\r\n")
f.write("\r\n")
f.write("initial\r\n")
f.write("   begin\r\n")
f.write("      $display(\" ===============================================\");\r\n")
f.write("      $display(\"|                 START SIMULATION              |\");\r\n")
f.write("      $display(\" ===============================================\");\r\n")
f.write("      // Disable automatic DMA verification\r\n")
f.write("      #10;\r\n")
f.write("      dma_verif_on = 0;\r\n")
f.write("\r\n")
f.write("      repeat(5) @(posedge mclk);\r\n")
f.write("      stimulus_done = 0;\r\n")
f.write("      \r\n")
f.write("      /* ----------------------  INITIALIZATION --------------- */\r\n")
f.write("\r\n")
f.write("      $display(\"waiting for foo entry...\");\r\n")
f.write("      while(~sm_0_executing) @(posedge mclk);\r\n")
f.write("      @(`FOO_SECRET);\r\n")
f.write("      if (`FOO_SECRET !== `FOO_SECRET_VAL) tb_error(\"====== FOO SECRET INIT ======\");\r\n")
f.write("\r\n")
f.write("      $display(\"waiting for DMA loop entry...\");\r\n")
f.write("      @(r15==16'h1000);\r\n")
f.write("      \r\n")
f.write("      /* ----------------------  DMA ACCESSES --------------- */\r\n")
f.write("      $display(\"DMA rd/wr foo data...\");\r\n")
f.write("      dma_read_16b(`FOO_SECRET_ADDR, 16'h0, /*fail=*/1);\r\n")
f.write("      dma_write_16b(`FOO_SECRET_ADDR, `FOO_SECRET_VAL+3, /*fail=*/1);\r\n")
f.write("      dma_read_16b(`FOO_SECRET_ADDR, 16'h0, /*fail=*/1);\r\n")
f.write("\r\n")
f.write("      $display(\"DMA rd/wr foo text...\");\r\n")
f.write("      dma_read_16b(`FOO_TEXT_ADDR, 16'h0, /*fail=*/1);\r\n")
f.write("      dma_write_16b(`FOO_TEXT_ADDR, `FOO_TEXT_VAL+3, /*fail=*/1);\r\n")
f.write("      dma_read_16b(`FOO_TEXT_ADDR, 16'h0, /*fail=*/1);\r\n")
f.write("\r\n")
f.write("      dma_write_16b(`DMA_DONE_ADDR, 1, /*fail=*/0);\r\n")
f.write("      \r\n")
f.write("      /* ----------------------  END OF TEST --------------- */\r\n")
f.write("      $display(\"waiting for end of test...\");\r\n")
f.write("      @(r15==16'h2000);\r\n")
f.write("\r\n")
f.write("      stimulus_done = 1;\r\n")
f.write("   end\r\n")

# Read instruction to generate memory tace for
# This assumes that the sllvm github repository is cloned into your home directory
with open('../../../../../../../build/sllvm/lib/Target/MSP430/MSP430GenInstrMemTraceInfo.inc') as f:
    all_instructions = [line.rstrip('\n') for line in f]

add_instr = all_instructions[258].split('{')[1].split('}')[0]
print(add_instr)

# create .s43 file for simulation
# -------------------------------
f= open("gen_mem_trace.s43","w+")

f.write("/*===========================================================================*/\r\n")
f.write("/*                 SANCUS MODULE DMA VIOLATION                               */\r\n")
f.write("/*---------------------------------------------------------------------------*/\r\n")
f.write("/* Test DMA violations by accessing secret SM memory from outside.           */\r\n")
f.write("/*                                                                           */\r\n")
f.write("/*---------------------------------------------------------------------------*/\r\n")
f.write("/*===========================================================================*/\r\n")
f.write("\r\n")
f.write(".include \"pmem_defs.asm\"\r\n")
f.write(".include \"sancus_macros.asm\"\r\n")
f.write("\r\n")
f.write(".set dma_done, DMEM_260\r\n")
f.write(".set foo_secret_start, DMEM_262\r\n")
f.write(".set foo_secret_end, DMEM_268\r\n")
f.write("\r\n")
f.write(".global main\r\n")
f.write("main:\r\n")
f.write("    " + add_instr + "    //added for memory trace generation\r\n")
f.write("    clr r15\r\n")
f.write("    mov r15, &dma_done\r\n")
f.write("    disable_wdt\r\n")
f.write("    eint\r\n")
f.write("    sancus_enable #1234, #foo_text_start, #foo_text_end, #foo_secret_start, #foo_secret_end\r\n")
f.write("    br #foo_text_start\r\n")
f.write("\r\n")
f.write("wait_for_dma:\r\n")
f.write("    mov #0x1000, r15\r\n")
f.write("1:  mov &dma_done, r14\r\n")
f.write("    tst r14\r\n")
f.write("    jz 1b\r\n")
f.write("\r\n")
f.write("    /* ----------------------         END OF TEST        --------------- */\r\n")
f.write("end_of_test:\r\n")
f.write("	mov #0x2000, r15\r\n")
f.write("fail_test:\r\n")
f.write("	br #0xffff\r\n")
f.write("\r\n")
f.write("    /* ----------------------         SANCUS MODULE      --------------- */\r\n")
f.write("\r\n")
f.write("foo_text_start:\r\n")
f.write("    mov #0xf00d, &foo_secret_start\r\n")
f.write("    br #wait_for_dma\r\n")
f.write("foo_text_value:\r\n")
f.write("    .word 0xcafe\r\n")
f.write("foo_text_end:\r\n")
f.write("\r\n")
f.write("    /* ----------------------         INTERRUPT VECTORS  --------------- */\r\n")
f.write("\r\n")
f.write(".section .vectors, \"a\"\r\n")
f.write(".word end_of_test  ; Interrupt  0 (lowest priority)    <unused>\r\n")
f.write(".word end_of_test  ; Interrupt  1                      <unused>\r\n")
f.write(".word end_of_test  ; Interrupt  2                      <unused>\r\n")
f.write(".word end_of_test  ; Interrupt  3                      <unused>\r\n")
f.write(".word end_of_test  ; Interrupt  4                      <unused>\r\n")
f.write(".word end_of_test  ; Interrupt  5                      <unused>\r\n")
f.write(".word end_of_test  ; Interrupt  6                      <unused>\r\n")
f.write(".word end_of_test  ; Interrupt  7                      <unused>\r\n")
f.write(".word end_of_test  ; Interrupt  8                      <unused>\r\n")
f.write(".word end_of_test  ; Interrupt  9                      TEST IRQ\r\n")
f.write(".word end_of_test  ; Interrupt 10                      Watchdog timer\r\n")
f.write(".word end_of_test  ; Interrupt 11                      <unused>\r\n")
f.write(".word end_of_test  ; Interrupt 12                      <unused>\r\n")
f.write(".word end_of_test  ; Interrupt 13                      SM_IRQ\r\n")
f.write(".word end_of_test  ; Interrupt 14                      NMI\r\n")
f.write(".word main         ; Interrupt 15 (highest priority)   RESET\r\n")




