#include "Vtb_openMSP430.h"

#include <verilated.h>
#include <verilated_vcd_c.h>

#include <memory>
#include <vector>
#include <iostream>
#include <fstream>

#include <cstdint>
#include <cassert>

#include <sys/select.h>
#include <sys/time.h>

#include <signal.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>

const double TIMESCALE       = 1e-9;
const int    CLOCK_FREQUENCY = 100*1e6;
const int    CLOCK_PERIOD    = 1/(CLOCK_FREQUENCY*TIMESCALE);

const std::uint64_t MAX_CYCLES = 1000000000ULL;

// class Memory
// {
// public:

//     Memory(Vtb_openMSP430& top, const char* memoryFile) : top_{top}
//     {
//         auto ifs = std::ifstream{memoryFile, std::ifstream::binary};
//         auto memoryBytes =
//             std::vector<unsigned char>{std::istreambuf_iterator<char>(ifs), {}};

//         assert((memoryBytes.size() % 4 == 0) &&
//                "Memory does not contain a multiple of words");

//         auto i = std::size_t{0};

//         while (i < memoryBytes.size())
//         {
//             auto b0 = memoryBytes[i++];
//             auto b1 = memoryBytes[i++];
//             auto b2 = memoryBytes[i++];
//             auto b3 = memoryBytes[i++];

//             auto word = b0 | (b1 << 8) | (b2 << 16) | (b3 << 24);
//             memory_.push_back(word);
//         }
//     }

//     bool eval()
//     {
//         auto updated = false;

//         if (top_.ibus_cmd_valid)
//         {
//             top_.ibus_rsp_valid = true;
//             top_.ibus_rsp_payload_rdata = read(top_.ibus_cmd_payload_address);
//             updated = true;
//         }

//         if (top_.dbus_cmd_valid)
//         {
//             top_.dbus_cmd_ready = true;

//             if (top_.dbus_cmd_payload_write)
//             {
//                 write(top_.dbus_cmd_payload_address,
//                       top_.dbus_cmd_payload_wmask,
//                       top_.dbus_cmd_payload_wdata);
//             }
//             else
//             {
//                 top_.dbus_rsp_valid = true;
//                 top_.dbus_rsp_payload_rdata =
//                     read(top_.dbus_cmd_payload_address);
//             }

//             updated = true;
//         }

//         return updated;
//     }

// private:

//     using Address = std::uint32_t;
//     using Word = std::uint32_t;
//     using Mask = std::uint8_t;

//     Word read(Address address)
//     {
//         ensureEnoughMemory(address);
//         return memory_[(address >> 2)];
//     }

//     void write(Address address, Mask mask, Word value)
//     {
//         ensureEnoughMemory(address);

//         auto bitMask = Word{0};
//         if (mask & 0x1) bitMask |= 0x000000ff;
//         if (mask & 0x2) bitMask |= 0x0000ff00;
//         if (mask & 0x4) bitMask |= 0x00ff0000;
//         if (mask & 0x8) bitMask |= 0xff000000;

//         auto& memoryValue = memory_[(address >> 2)];
//         memoryValue &= ~bitMask;
//         memoryValue |= value & bitMask;
//     }

//     void ensureEnoughMemory(Address address)
//     {
//         if ((address >> 2) >= memory_.size())
//         {
//             memory_.reserve((address >> 2) + 1);

//             while ((address >> 2) >= memory_.size())
//                 memory_.push_back(0xcafebabe);
//         }
//     }

//     Vtb_openMSP430& top_;
//     std::vector<Word> memory_;
// };

// class CharDev
// {
// public:

//     CharDev(Vtb_openMSP430& top) : top_{top}, gotEot_{false}
//     {
//     }

//     void eval()
//     {
//         if (top_.charOut_valid)
//         {
//             auto charOut = char(top_.charOut_payload);

//             if (charOut == 0x4)
//                 gotEot_ = true;
//             else
//             {
//                 gotEot_ = false;
//                 std::cout << charOut;
//             }
//         }
//     }

//     bool gotEot() const
//     {
//         return gotEot_;
//     }

// private:

//     Vtb_openMSP430& top_;
//     bool gotEot_;
// };

// class TestDev
// {
// public:

//     TestDev(Vtb_openMSP430& top) : top_{top}, result_{-1}
//     {
//     }

//     void eval()
//     {
//         if (top_.testOut_valid)
//             result_ = top_.testOut_payload;
//     }

//     bool gotResult() const
//     {
//         return result_ >= 0;
//     }

//     bool hasFailed() const
//     {
//         return gotResult() && result_ != 0;
//     }

//     int failedTest() const
//     {
//         assert(hasFailed() && "No failed tests");
//         return result_;
//     }

// private:

//     Vtb_openMSP430& top_;
//     int result_;
// };

// class ByteDev
// {
// public:

//     ByteDev(Vtb_openMSP430& top) : top_{top}
//     {
//     }

//     bool eval()
//     {
//         if (top_.reset)
//             return false;

//         top_.byteIo_rdata_valid = false;

//         if (top_.byteIo_wdata_valid)
//         {
//             auto charOut = char(top_.byteIo_wdata_payload);
//             std::cout << charOut;
//         }

//         if (!hasStdinByte && stdinAvailable())
//         {
//             currentStdinByte = std::cin.get();
//             hasStdinByte = !std::cin.eof();
//         }

//         if (hasStdinByte)
//         {
//             top_.byteIo_rdata_valid = true;
//             top_.byteIo_rdata_payload = currentStdinByte;

//             if (top_.byteIo_rdata_ready)
//                 hasStdinByte = false;

//             return true;
//         }

//         return false;
//     }

// private:

//     bool stdinAvailable() const
//     {
//         if (std::cin.eof())
//             return false;

//         fd_set rfds;
//         FD_ZERO(&rfds);
//         FD_SET(STDIN_FILENO, &rfds);

//         timeval tv;
//         tv.tv_sec = 0;
//         tv.tv_usec = 0;

//         int result = select(1, &rfds, nullptr, nullptr, &tv);
//         return result == 1;
//     }

//     Vtb_openMSP430& top_;
//     char currentStdinByte;
//     bool hasStdinByte = false;
// };

auto tracer = std::unique_ptr<VerilatedVcdC>{new VerilatedVcdC};

void exit_handler(int s){
    tracer->close();
    printf("Program aborted\n");
    exit(1); 

}

int main(int argc, char** argv)
{
    // assert(argc >= 2 && "No memory file name given");

    Verilated::commandArgs(argc, argv);

    auto top = std::unique_ptr<Vtb_openMSP430>{new Vtb_openMSP430};
    top->tb_openMSP430__DOT__reset_n = 1;
    top->tb_openMSP430__DOT__dco_clk = 1;
    top->tb_openMSP430__DOT__dco_local_enable = 1;

    // auto memoryFile = argv[argc - 1];
    // auto memory = Memory{*top, memoryFile};
    // auto charDev = CharDev{*top};
    // auto testDev = TestDev{*top};
    // auto byteDev = ByteDev{*top};

    Verilated::traceEverOn(true);
    top->trace(tracer.get(), 99);
    tracer->open("sim.vcd");

    vluint64_t mainTime = 0;
    auto isDone = false;
    int result = 0;


    // Register sigabort handler to finish writing vcd file
    struct sigaction sigIntHandler; 
    sigIntHandler.sa_handler = exit_handler;
    sigemptyset(&sigIntHandler.sa_mask);
    sigIntHandler.sa_flags = 0;
    sigaction(SIGINT, &sigIntHandler, NULL);


    while (!isDone)
    {
        auto clockEdge = (mainTime % (CLOCK_PERIOD/2) == 0);

        if (clockEdge){
            top->tb_openMSP430__DOT__dco_clk = !top->tb_openMSP430__DOT__dco_clk;
        }


        if (mainTime >= 5*CLOCK_PERIOD)
            top->tb_openMSP430__DOT__reset_n = 0;

        top->eval();

        if (clockEdge && top->tb_openMSP430__DOT__dco_clk)
        {
            // if (memory.eval())
            //     top->eval();

            // charDev.eval();
            // testDev.eval();

            // if (charDev.gotEot())
            //     isDone = true;

            // if (testDev.gotResult())
            // {
            //     isDone = true;

            //     if (testDev.hasFailed())
            //     {
            //         std::cerr << "Test " << testDev.failedTest() << " failed\n";
            //         result = 1;
            //     }
            //     else
            //         std::cout << "All tests passed\n";
            // }

            // if (byteDev.eval())
            //     top->eval();

            if (mainTime >= MAX_CYCLES*CLOCK_PERIOD)
            {
                isDone = true;
                result = 1;
            }
        }

        tracer->dump(mainTime);

        mainTime++;
    }

    tracer->close();
    return result;
}
