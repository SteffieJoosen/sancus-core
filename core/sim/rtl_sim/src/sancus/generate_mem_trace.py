#!/usr/bin/env python3

import os
import sys

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

def create_v_file():
    # create .v file for simulation
    # -----------------------------

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

    f.close()

def create_s43_file(instr):
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
    for i in instr:
        f.write("    " + i + "\r\n") # + "    //added for memory trace generation\r\n")
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

    f.close()


def generate_instruction(instr_number):

    create_v_file()
    # Read instruction to generate memory tace for
    # This assumes that the sllvm github repository is cloned into your home directory
    with open('../../../../../../../build/sllvm/lib/Target/MSP430/MSP430GenInstrMemTraceInfo.inc') as f:
        all_instructions = [line.rstrip('\n') for line in f]

    instr = all_instructions[instr_number].split('{')[1].split('}')[0].split("; ")

    create_s43_file(instr)


    # run the simulation, which result in the newly generated tb_openMSP430.vcd file
    os.system('cd ../../run && ./run sancus/gen_mem_trace')

    os.system('echo \"--------------------------------------\"')
    os.system('echo \"---- TEX FILE IS BEING GENERATED -----\"')
    os.system('echo \"--------------------------------------\"')

    # run the vcdvis script to generate the tex file containing the traces
    os.system('cd ~/vcdvis && '
              './vcdvis.py -start_tick 1000ns -end_tick 1400ns -f '
              '~/sllvm/sancus-main/sancus-core/core/sim/rtl_sim/run/tb_openMSP430.vcd latex'
              ' > ' + sys.path[0] + '/Traces.tex')

    length = file_len("Traces.tex")

    traces = open("Traces.tex", "r")
    list_of_lines = traces.readlines()
    list_of_lines.insert(length-3, "\caption{" + instr +"}\r\n")

    traces = open("Traces.tex", "w")
    traces.writelines(list_of_lines)
    traces.close()

    os.system('cd ~/vcdvis && '
              'awk \'NR==4, NR==' + str(length) + ' {print $0}\' '
              + sys.path[0] + '/Traces.tex >> ' + sys.path[0] + '/traces.tex')

    return


if os.path.exists("traces.tex"):
    os.remove("traces.tex")
if os.path.exists("Traces.tex"):
    os.remove("Traces.tex")
if os.path.exists("./traces_pdf"):
    os.remove("./traces_pdf")
if os.path.exists("gen_mem_trace.v"):
    os.remove("gen_mem_trace.v")
if os.path.exists("gen_mem_trace.s43"):
    os.remove("gen_mem_trace.s43")

# create tex file to dump the traces in
# -------------------------------------

traces_file = open("traces.tex", "w+")

traces_file.write("\documentclass{article}\r\n")
traces_file.write("\\usepackage{tikz}\r\n")
traces_file.write("\r\n")
traces_file.write("\\begin{document}\r\n")

traces_file.close()

generate_instruction(258)



traces_file = open("traces.tex", "a")

traces_file.write("\\end{document}\r\n")
traces_file.close()
