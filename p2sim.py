from __future__ import print_function
import os
import re
import math as m

# global variable to hold something-in-somthing-SA-
unnamedSA = []
# Function List:
# 1. netRead: read the benchmark file and build circuit netlist
# 2. gateCalc: function that will work on the logic of each gate
# 3. inputRead: function that will update the circuit dictionary made in netRead to hold the line values
# 4. basic_sim: the actual simulation
# 5. main: The main function


# -------------------------------------------------------------------------------------------------------------------- #
# dictionary to store all test vectors for each TV set
TV_map = {}
MAX_BATCH = 25


# get the input size
def get_input_size(circFile):
    for line in circFile:
        # NOT Reading any empty lines
        if (line == "\n"):
            continue

        # Find the number of inputs line
        if (line.find("inputs") != -1):
            N_line = line
            break

    # Get the integer from N_line
    N = int(re.search(r'\d+', N_line).group())
    return N


# LFSR simulator
def LFSR(seed):
    binary = []
    rev_binary = []
    # if seed is from 0-9, concatanate a 0 before the intger
    if len(seed) < 2:
        binary.insert(0, "0000")
    # turn each hex value in seed indices into binary in reverse order and insert to list
    for i in seed:
        binary.insert(0, '{:04b}'.format(int(i, 16))[::-1])

    # combine the values in list into one, then segment each index into a list
    binary = list(''.join(map(str, binary)))
    doppelganger = binary
    N_size = len(binary)
    lsb = binary[N_size - 1]

    # LFSR operation with an exclusive or at circuit line 2, 3, 4
    for x in range(N_size - 1, -1, -1):
        if x == 2 or x == 3 or x == 4:
            binary[x] = str(int(doppelganger[x - 1]) ^ int(lsb))
            continue
        if x == 0:
            binary[x] = lsb
            break

        binary[x] = binary[x - 1]

    # convert resulting binary into hex after joining the list to one string
    binary = hex(int(''.join(map(str, binary[0:4])), 2)).replace("0x", "") + \
             hex(int(''.join(map(str, binary[4:])), 2)).replace("0x", "")

    # turn each hex value in seed indices into binary in reverse order and insert to list
    for i in binary:
        rev_binary.insert(0, '{:04b}'.format(int(i, 16))[::-1])

    # combine the values in list into one string
    rev_binary = ''.join(map(str, rev_binary))
    binary = rev_binary

    # convert binary to hex
    hexa = hex(int(rev_binary[0:4], 2)).replace("0x", "") + \
           hex(int(rev_binary[4:], 2)).replace("0x", "")

    return hexa, binary


# generate the test vectors for each sets
def generate_TV(init_seed, inputName, outputNameList):
    circFile = open(inputName, "r")

    N = get_input_size(circFile)

    # Compute the overhead of N groupings of 8 for vector size
    vector_size = m.ceil(N / 8)

    for tv in outputNameList:
        # if (tv != "TV_E.txt"):
        #     continue
        print("Generating " + tv + " ........ ", end='')

        # Used to store all the test vectors of a certain set
        arr = []

        # Vector of size N inputs; used as the storage of hex outputs for each counters/LFSR
        TV = [0] * vector_size

        # Vector of size N inputs; used as the storege of binary outputs for each counters/LFSR
        TV_bin = [0] * vector_size

        # Used to store binary seeds
        seed_bin = []

        # Used for TV_A, TV_B, and TV_C to mark the x value as the capping point where the binary reached over 255
        cap = 0

        outputFile = open(tv, "w")
        seed = init_seed

        if tv == "TV_A.txt":
            # increment seed by 1 to a single counter and write to file
            for x in range(0, 255, 1):
                if ((seed + x - cap) <= 255):
                    TV[vector_size - 1] = seed + x - cap
                else:
                    TV[vector_size - 1] = 0
                    seed = 0
                    cap = x

                for i, val in enumerate(TV):
                    TV_bin[i] = "{0:b}".format(val).zfill(8)
                arr.append("".join(map(str, TV_bin)))
                outputFile.write("".join(map(str, TV_bin)) + "\n")
            TV_map[tv] = arr
        elif tv == "TV_B.txt":
            # increment seed by 1 to multiple counters and write to file
            for x in range(0, 255, 1):
                if ((seed + x - cap) <= 255):
                    TV[0:] = [seed + x - cap] * (vector_size)
                else:
                    TV[0:] = [0] * (vector_size)
                    seed = 0
                    cap = x

                for i, val in enumerate(TV):
                    TV_bin[i] = "{0:b}".format(val).zfill(8)
                arr.append("".join(map(str, TV_bin)))
                outputFile.write("".join(map(str, TV_bin)) + "\n")
            TV_map[tv] = arr
        elif tv == "TV_C.txt":
            # stores the previous TV set
            temp = [0] * vector_size

            # do a pre-run to fill temp list
            rec = (vector_size - 1)
            for i in range(vector_size - 1, -1, -1):
                if (seed + (rec - i) <= 255):
                    TV[i] = seed + (rec - i)
                    temp[i] = TV[i]
                else:
                    TV[i] = 0
                    temp[i] = TV[i]
                    seed = 0
                    rec = rec - 1

                for i, val in enumerate(TV):
                    TV_bin[i] = "{0:b}".format(val).zfill(8)
            arr.append("".join(map(str, TV_bin)))
            outputFile.write("".join(map(str, TV_bin)) + "\n")

            # perform calculation using previous TV values from temp
            for x in range(0, 254, 1):
                for i in range(vector_size - 1, -1, -1):
                    if ((temp[i] + 1) <= 255):
                        TV[i] = temp[i] + 1
                        temp[i] = TV[i]
                    else:
                        TV[i] = 0
                        temp[i] = TV[i]
                    for i, val in enumerate(TV):
                        TV_bin[i] = "{0:b}".format(val).zfill(8)
                arr.append("".join(map(str, TV_bin)))
                outputFile.write("".join(map(str, TV_bin)) + "\n")
                
            TV_map[tv] = arr
            # rec = vector_size - 1
            # # increment seed by 1 to multiple counters with +1 seed for each counter and write to file
            # for x in range(0, 255, 1):
            #     for i in range(vector_size - 1, -1, -1):
            #         if ((seed + (rec - i) + x - cap) <= 255):
            #             TV[i] = seed + (rec - i) + x - cap
            #         else:
            #             TV[i] = 0
            #             seed = 0
            #             cap = x
            #             rec = vector_size - 2

            #     for i, val in enumerate(TV):
            #         TV_bin[i] = "{0:b}".format(val).zfill(8)
            #     arr.append("".join(map(str, TV_bin)))
            #     outputFile.write("".join(map(str, TV_bin)) + "\n")
            # TV_map[tv] = arr
        elif tv == "TV_D.txt":
            ctr = 1
            seed_hex = hex(init_seed).replace("0x", "")

            # if seed is from 0-9, concatanate a 0 before the intger
            if len(seed_hex) < 2:
                seed_bin.append("0000")
            # turn each hex value in seed indices into binary and insert to list
            for i in seed_hex:
                seed_bin.append('{:04b}'.format(int(i, 16)))

            seed_bin = "".join(map(str, seed_bin))

            # run multiple LFSR with similar seeds for each LFSR and write to file
            while (ctr < 256):
                # for i in range(0, vector_size, 1): TV[i] = str(seed_hex).upper()          # for hex seeds
                for i in range(0, vector_size, 1): TV[i] = seed_bin
                arr.append("".join(map(str, TV)))
                outputFile.write("".join(map(str, TV)) + "\n")
                seed_hex, seed_bin = LFSR(str(seed_hex))
                ctr += 1
            TV_map[tv] = arr
        elif tv == "TV_E.txt":
            ctr = 1
            seed_hex = hex(init_seed).replace("0x", "")

            # if seed is from 0-9, concatanate a 0 before the intger
            if len(seed_hex) < 2:
                seed_bin.append("0000")
            # turn each hex value in seed indices into binary and insert to list
            for i in seed_hex:
                seed_bin.append('{:04b}'.format(int(i, 16)))

            seed_bin = "".join(map(str, seed_bin))

            # do a pre-run to have a filled TV list
            for i in range(vector_size - 1, -1, -1):
                TV[i] = str(seed_hex).upper()  # for hex seeds
                TV_bin[i] = seed_bin
                seed_hex, seed_bin = LFSR(str(seed_hex))

            arr.append("".join(map(str, TV_bin)))
            outputFile.write("".join(map(str, TV_bin)) + "\n")

            # run multiple LFSR with different seed for each LFSR and write to file
            while (ctr < 255):
                for i in range(vector_size - 1, -1, -1):
                    TV[i], seed_bin = LFSR(TV[i])
                    TV_bin[i] = seed_bin
                    TV[i] = TV[i].upper()
                arr.append("".join(map(str, TV_bin)))
                outputFile.write("".join(map(str, TV_bin)) + "\n")
                ctr += 1
            TV_map[tv] = arr
        print("COMPLETE: generated " + tv)
        outputFile.close()


def TV_gen():
    while (True):
        user_seed = input("Choose a seed in [1, 255] or enter 'q' to quit: ")
        if (user_seed == "q"):
            print("Bye!")
            return

        try:
            init_seed = int(user_seed)
        except:
            print("ERROR: Please type valid input -_- ..|.,\n")
            continue

        if (init_seed > 255 or init_seed < 1):
            print("ERROR: Invalid seed value\n")
            continue
        else:
            break

    # Used for file access
    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in

    # Select circuit benchmark file, default is circuit.bench
    while True:
        cktFile = "c432.bench"
        print("\n Read circuit benchmark file: use " + cktFile + "?" + " Enter to accept or type filename: ")
        userInput = input()
        if userInput == "":
            break
        else:
            cktFile = os.path.join(script_dir, userInput)
            if not os.path.isfile(cktFile):
                print("File does not exist. \n")
            else:
                break
    print("\ninput file: " + cktFile)

    TV_names = ["TV_A.txt", "TV_B.txt", "TV_C.txt", "TV_D.txt", "TV_E.txt"]
    print("output files: " + " ".join(map(str, TV_names)))
    print("\nProcessing...\n")

    generate_TV(int(init_seed), cktFile, TV_names)

    print("\nDone.")


# FUNCTION: Reading in the Circuit gate-level netlist file:
def netRead(netName):
    # Opening the netlist file:
    netFile = open(netName, "r")

    # temporary variables
    inputs = []  # array of the input wires
    outputs = []  # array of the output wires
    gates = []  # array of the gate list
    inputBits = 0  # the number of inputs needed in this given circuit
    faults = []

    # main variable to hold the circuit netlist, this is a dictionary in Python, where:
    # key = wire name; value = a list of attributes of the wire
    circuit = {}

    # Reading in the netlist file line by line
    for line in netFile:
        # NOT Reading any empty lines
        if (line == "\n"):
            continue

        # Removing spaces and newlines
        line = line.replace(" ", "")
        line = line.replace("\n", "")
        line = line.upper()
        # NOT Reading any comments
        if (line[0] == "#"):
            continue

        # @ Here it should just be in one of these formats:
        # INPUT(x)
        # OUTPUT(y)
        # z=LOGIC(a,b,c,...)

        # Read a INPUT wire and add to circuit:
        if (line[0:5] == "INPUT"):
            # Removing everything but the line variable name
            line = line.replace("INPUT", "")
            line = line.replace("(", "")
            line = line.replace(")", "")

            # part1 add 1 pair of SA's
            faults.append(line + "-SA-0")
            faults.append(line + "-SA-1")

            # Format the variable name to wire_*VAR_NAME*
            line = "wire_" + line

            # Error detection: line being made already exists
            if line in circuit:
                msg = "NETLIST ERROR: INPUT LINE \"" + line + "\" ALREADY EXISTS PREVIOUSLY IN NETLIST"
                print(msg + "\n")
                return msg

            # Appending to the inputs array and update the inputBits
            inputs.append(line)

            # add this wire as an entry to the circuit dictionary
            circuit[line] = ["INPUT", line, False, 'U']

            inputBits += 1
            print(line)
            print(circuit[line])
            continue

        # Read an OUTPUT wire and add to the output array list
        # Note that the same wire should also appear somewhere else as a GATE output
        if line[0:6] == "OUTPUT":
            # Removing everything but the numbers
            line = line.replace("OUTPUT", "")
            line = line.replace("(", "")
            line = line.replace(")", "")

            # Appending to the output array
            outputs.append("wire_" + line)
            continue

        # Read a gate output wire, and add to the circuit dictionary
        lineSpliced = line.split("=")  # splicing the line at the equals sign to get the gate output wire
        gateOut = "wire_" + lineSpliced[0]
        tempOut = lineSpliced[0]
        # Error detection: line being made already exists
        if gateOut in circuit:
            msg = "NETLIST ERROR: GATE OUTPUT LINE \"" + gateOut + "\" ALREADY EXISTS PREVIOUSLY IN NETLIST"
            print(msg + "\n")
            return msg

        # Appending the dest name to the gate list
        gates.append(gateOut)

        lineSpliced = lineSpliced[1].split("(")  # splicing the line again at the "("  to get the gate logic
        logic = lineSpliced[0].upper()

        lineSpliced[1] = lineSpliced[1].replace(")", "")
        terms = lineSpliced[1].split(",")  # Splicing the the line again at each comma to the get the gate terminals

        # part1 add 1 pair of SA's
        faults.append(tempOut + "-SA-0")
        faults.append(tempOut + "-SA-1")
        for INS in terms:
            faults.append(tempOut + "-IN-" + INS + "-SA-0")
            faults.append(tempOut + "-IN-" + INS + "-SA-1")

        # Turning each term into an integer before putting it into the circuit dictionary
        terms = ["wire_" + x for x in terms]

        # add the gate output wire to the circuit dictionary with the dest as the key
        circuit[gateOut] = [logic, terms, False, 'U']
        print(gateOut)
        print(circuit[gateOut])

    # now after each wire is built into the circuit dictionary,
    # add a few more non-wire items: input width, input array, output array, gate list
    # for convenience

    circuit["INPUT_WIDTH"] = ["input width:", inputBits]
    circuit["INPUTS"] = ["Input list", inputs]
    circuit["OUTPUTS"] = ["Output list", outputs]
    circuit["GATES"] = ["Gate list", gates]
    circuit["FAULTS"] = ["Full Faults", faults]

    print("\n bookkeeping items in circuit: \n")
    print(circuit["INPUT_WIDTH"])
    print(circuit["INPUTS"])
    print(circuit["OUTPUTS"])
    print(circuit["GATES"])
    print(circuit["FAULTS"])

    return circuit


# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: calculates the output value for each logic gate
def gateCalc(circuit, node):
    # terminal will contain all the input wires of this logic gate (node)
    terminals = list(circuit[node][1])

    holdTheWire = "Undefined"
    # temporarily changes a wire's value for -in-SA
    if len(unnamedSA) > 0:
        if node == unnamedSA[0]:  # if same output wire of gate as SA
            for term in terminals:  # find the input terminal that is SA
                if term == unnamedSA[1]:
                    holdTheWire = list(circuit[term]).copy()  # copy the wire attributes before change
                    circuit[term][3] = unnamedSA[2]  # change bit value of wire
                    continue

    # If the node is an Inverter gate output, solve and return the output
    if circuit[node][0] == "NOT":
        if circuit[terminals[0]][3] == '0':
            circuit[node][3] = '1'
        elif circuit[terminals[0]][3] == '1':
            circuit[node][3] = '0'
        elif circuit[terminals[0]][3] == "U":
            circuit[node][3] = "U"
        else:  # Should not be able to come here
            circuit = copycircuit(circuit, holdTheWire)
            return -1
        circuit = copycircuit(circuit, holdTheWire)
        return circuit

    # If the node is an Buffer gate output, solve and return the output
    elif circuit[node][0] == "BUFF":
        if circuit[terminals[0]][3] == '0':
            circuit[node][3] = '0'
        elif circuit[terminals[0]][3] == '1':
            circuit[node][3] = '1'
        elif circuit[terminals[0]][3] == "U":
            circuit[node][3] = "U"
        else:  # Should not be able to come here
            circuit = copycircuit(circuit, holdTheWire)
            return -1
        circuit = copycircuit(circuit, holdTheWire)
        return circuit

    # If the node is an AND gate output, solve and return the output
    elif circuit[node][0] == "AND":
        # Initialize the output to 1
        circuit[node][3] = '1'
        # Initialize also a flag that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 0 at any input terminal, AND output is 0. If there is an unknown terminal, mark the flag
        # Otherwise, keep it at 1
        for term in terminals:
            if circuit[term][3] == '0':
                circuit[node][3] = '0'
                break
            if circuit[term][3] == "U":
                unknownTerm = True

        if unknownTerm:
            if circuit[node][3] == '1':
                circuit[node][3] = "U"
        circuit = copycircuit(circuit, holdTheWire)
        return circuit

    # If the node is a NAND gate output, solve and return the output
    elif circuit[node][0] == "NAND":
        # Initialize the output to 0
        circuit[node][3] = '0'
        # Initialize also a variable that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 0 terminal, NAND changes the output to 1. If there is an unknown terminal, it
        # changes to "U" Otherwise, keep it at 0
        for term in terminals:
            if circuit[term][3] == '0':
                circuit[node][3] = '1'
                break
            if circuit[term][3] == "U":
                unknownTerm = True
                break

        if unknownTerm:
            if circuit[node][3] == '0':
                circuit[node][3] = "U"
        circuit = copycircuit(circuit, holdTheWire)
        return circuit

    # If the node is an OR gate output, solve and return the output
    elif circuit[node][0] == "OR":
        # Initialize the output to 0
        circuit[node][3] = '0'
        # Initialize also a variable that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 1 terminal, OR changes the output to 1. Otherwise, keep it at 0
        for term in terminals:
            if circuit[term][3] == '1':
                circuit[node][3] = '1'
                break
            if circuit[term][3] == "U":
                unknownTerm = True

        if unknownTerm:
            if circuit[node][3] == '0':
                circuit[node][3] = "U"
        circuit = copycircuit(circuit, holdTheWire)
        return circuit

    # If the node is an NOR gate output, solve and return the output
    if circuit[node][0] == "NOR":
        # Initialize the output to 1
        circuit[node][3] = '1'
        # Initialize also a variable that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 1 terminal, NOR changes the output to 0. Otherwise, keep it at 1
        for term in terminals:
            if circuit[term][3] == '1':
                circuit[node][3] = '0'
                break
            if circuit[term][3] == "U":
                unknownTerm = True
        if unknownTerm:
            if circuit[node][3] == '1':
                circuit[node][3] = "U"
        circuit = copycircuit(circuit, holdTheWire)
        return circuit

    # If the node is an XOR gate output, solve and return the output
    if circuit[node][0] == "XOR":
        # Initialize a variable to zero, to count how many 1's in the terms
        count = 0

        # if there are an odd number of terminals, XOR outputs 1. Otherwise, it should output 0
        for term in terminals:
            if circuit[term][3] == '1':
                count += 1  # For each 1 bit, add one count
            if circuit[term][3] == "U":
                circuit[node][3] = "U"
                circuit = copycircuit(circuit, holdTheWire)
                return circuit

        # check how many 1's we counted
        if count % 2 == 1:  # if more than one 1, we know it's going to be 0.
            circuit[node][3] = '1'
        else:  # Otherwise, the output is equal to how many 1's there are
            circuit[node][3] = '0'
        circuit = copycircuit(circuit, holdTheWire)
        return circuit

    # If the node is an XNOR gate output, solve and return the output
    elif circuit[node][0] == "XNOR":
        # Initialize a variable to zero, to count how many 1's in the terms
        count = 0

        # if there is a single 1 terminal, XNOR outputs 0. Otherwise, it outputs 1
        for term in terminals:
            if circuit[term][3] == '1':
                count += 1  # For each 1 bit, add one count
            if circuit[term][3] == "U":
                circuit[node][3] = "U"
                circuit = copycircuit(circuit, holdTheWire)
                return circuit

        # check how many 1's we counted
        if count % 2 == 1:  # if more than one 1, we know it's going to be 0.
            circuit[node][3] = '0'
        else:  # Otherwise, the output is equal to how many 1's there are
            circuit[node][3] = '1'
        circuit = copycircuit(circuit, holdTheWire)
        return circuit

    circuit = copycircuit(circuit, holdTheWire)
    # Error detection... should not be able to get at this point
    return circuit[node][0]


# function used above to clear the global with something-in-something-sA and copy back to circuit after simulation
def copycircuit(circuit, holdTheWire):
    global unnamedSA
    if holdTheWire != "Undefined":
        circuit[unnamedSA[1]] = list(holdTheWire).copy()
    return circuit


# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: Updating the circuit dictionary with the input line, and also resetting the gates and output lines
def inputRead(circuit, line):
    line = line.rstrip()
    # Checking if input bits are enough for the circuit
    if len(line) < circuit["INPUT_WIDTH"][1]:
        return -1

    # Getting the proper number of bits:
    line = line[(len(line) - circuit["INPUT_WIDTH"][1]):(len(line))]

    # Adding the inputs to the dictionary
    # Since the for loop will start at the most significant bit, we start at input width N
    i = circuit["INPUT_WIDTH"][1] - 1
    inputs = list(circuit["INPUTS"][1])
    # dictionary item: [(bool) If accessed, (int) the value of each line, (int) layer number, (str) origin of U value]
    for bitVal in line:
        bitVal = bitVal.upper()  # in the case user input lower-case u
        circuit[inputs[i]][3] = bitVal  # put the bit value as the line value
        circuit[inputs[i]][2] = True  # and make it so that this line is accessed

        # In case the input has an invalid character (i.e. not "0", "1" or "U"), return an error flag
        if bitVal != "0" and bitVal != "1" and bitVal != "U":
            breakpoint()
            return -2
        i -= 1  # continuing the increments

    return circuit


# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: the actual simulation #
def basic_sim(circuit):
    # QUEUE and DEQUEUE
    # Creating a queue, using a list, containing all of the gates in the circuit
    queue = list(circuit["GATES"][1])
    i = 1

    while True:
        i -= 1
        # If there's no more things in queue, done
        if len(queue) == 0:
            break

        # Remove the first element of the queue and assign it to a variable for us to use
        curr = queue[0]
        queue.remove(curr)

        # initialize a flag, used to check if every terminal has been accessed
        term_has_value = True

        # Check if the terminals have been accessed
        for term in circuit[curr][1]:
            if not circuit[term][2]:
                term_has_value = False
                break

        ##part2 skip this cuz this is a SA wire
        if circuit[curr][2] == True:
            continue

        if term_has_value:
            circuit[curr][2] = True
            circuit = gateCalc(circuit, curr)

            # ERROR Detection if LOGIC does not exist
            if isinstance(circuit, str):
                print(circuit)
                return circuit

            # print("Progress: updating " + curr + " = " + circuit[curr][3] + " as the output of " + circuit[curr][0] + " for:")
            # for term in circuit[curr][1]:
            #    print(term + " = " + circuit[term][3])
            # print("\nPress Enter to Continue...")
            # input()

        else:
            # If the terminals have not been accessed yet, append the current node at the end of the queue
            queue.append(curr)
    global unnamedSA
    unnamedSA = []
    return circuit


# this will update the circuit list will the fault found in the line passed into the function
def readFaults(line, circuit):
    line = line.split("-")
    if (len(line) == 3):
        circuit["wire_" + line[0]][2] = True
        circuit["wire_" + line[0]][3] = line[2]
    elif (len(line) == 5):
        global unnamedSA
        unnamedSA = []
        unnamedSA = ["wire_" + line[0], "wire_" + line[2], line[4]]
    return circuit


# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: read_flist
def read_flist(flist_Input):
    flistFile = open(flist_Input, "r")
    fault_list = list()

    for line in flistFile:
        if (line == "\n"):
            continue
        if (line[0] == "#"):
            continue
        # Removing the the newlines at the end and then output it to the txt file
        line = line.replace("\n", "")
        # Removing spaces
        line = line.replace(" ", "")
        line = line.upper()
        fault_list.append(line)

    flistFile.close()
    return fault_list


# reset the circuit for a new simulation
def resetCircuit(circuit):
    for key in circuit:
        if (key[0:5] == "wire_"):
            circuit[key][2] = False
            circuit[key][3] = 'U'
    return circuit


# function that will loop through all faults and simulate SA faults <----------------
def sa_Fault_Simulator(flist, circuit, line, newCircuit, output):
    detectedFaults = []
    detectedouputs = []
    # simulate for each SA fault
    # line will have current TV #aFault will have current SA fault
    for aFault in flist:
        # print("\n ---> Now ready to simulate INPUT = " + line + "@" + aFault)
        # circuit = newCircuit
        circuit = inputRead(circuit, line)
        if circuit == -1:
            print("INPUT ERROR: INSUFFICIENT BITS")
            # outputFile.write(" -> INPUT ERROR: INSUFFICIENT BITS" + "\n")
            # After each input line is finished, reset the netList
            circuit = newCircuit
            print("...move on to next input\n")
            continue
        elif circuit == -2:
            print("INPUT ERROR: INVALID INPUT VALUE/S")
            # outputFile.write(" -> INPUT ERROR: INVALID INPUT VALUE/S" + "\n")
            # After each input line is finished, reset the netList
            circuit = newCircuit
            print("...move on to next input\n")
            continue
        # simulate faults and calculate output
        circuit = readFaults(aFault, circuit)
        circuit = basic_sim(circuit)
        # print("\n *** Finished simulation - resulting circuit: \n")
        # print(circuit)
        SA_output = ""  # create a variable to hold the output of the SA fault
        for y in circuit["OUTPUTS"][1]:
            if not circuit[y][2]:
                SA_output = "NETLIST ERROR: OUTPUT LINE \"" + y + "\" NOT ACCESSED"
                break
            SA_output = str(circuit[y][3]) + SA_output

        # print("\n *** Summary of simulation: ")
        # print(aFault+ " @" + line + " -> " + SA_output + " written into output file. \n")
        # outputFile.write(aFault + " @" + line + " -> " + SA_output + "\n")
        if output != SA_output:
            detectedFaults.append(aFault)
            detectedouputs.append(SA_output)
        # After each input line is finished, reset the circuit
        # print("\n *** Now resetting circuit back to unknowns... \n")
        resetCircuit(circuit)
    return [detectedFaults, detectedouputs]


# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: This fucntion is only related to project 4
def Project4():
    print("Welecom to Sequential Circuits Sim !!\n")

    print("Please Enter the sequential benchmark file:\n")
    SeqCircuit = SeqBenchmark("f_adder.bench")

    SeqCircuit = netRead(SeqCircuit)
    inputNum = SeqCircuit['INPUT_WIDTH'][1]

    print("\nPlease Enter a Test Vector t in integer (Press enter to select the deafult: t=0): \n")
    testVector = input()
    if testVector =="":
        testVector = testVector.zfill(inputNum)
    else:
        testVector = int(testVector)
        testVector = bindigits(testVector, inputNum)

    print("\nPlease Enter Numbers of cycles (Press enter to select the deafult: n=5): \n")
    n = input()
    if n =="":
        n = 5
    else:
        n = int(n)

    inputRead(SeqCircuit, testVector)

    for i in range(0,n):
        basic_sim(SeqCircuit)


    print("\nPlease Enter Numbers of cycles (Press enter to select the deafult: stuck-at-0): \n")
    fault_f = input()
    if fault_f == "":
        fault_f = SeqCircuit['FAULTS'][1][0]

    print("\n")

# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: Takes int and return bin
def intToBin(intNum, inputNumb):
    s = bin(intNum & int("1"*inputNumb, 2))[2:]
    return ("{0:0>%s}" % (bits)).format(s)

    

# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: function takes and return the seq circuit bennchmark file.
def SeqBenchmark(defFile):
    # Used for file access
    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in

    # Select circuit benchmark file, default is circuit.bench
    while True:
        cktFile = defFile
        print("Read circuit benchmark file: use " + defFile + "?" + " Enter to accept or type filename: ")
        userInput = input()
        if userInput == "":
            return defFile
        else:
            cktFile = os.path.join(script_dir, userInput)
            if not os.path.isfile(cktFile):
                print("File does not exist. \n")
            else:
                return userInput

# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: Main Function
def main():
    # **************************************************************************************************************** #
    # NOTE: UI code; Does not contain anything about the actual simulation

    # menu
    while (True):
        user_select = input("\nChoose what you'd like to do (1, 2, or 3):" + \
                            "\n1: Test Vector Generation" + \
                            "\n2: Fault Coverage Simulation" + \
                            "\n3: (extra credit) Avg Fault Coverage data generation" + \
                            "\n4: Sequential Circuits Sim" + \
                            "\n5: Quit\n")

        try:
            selection = int(user_select)
        except:
            print("ERROR: Please type valid input -_- ..|.,\n")
            continue

        if (selection > 4 or selection < 1):
            print("ERROR: Invalid selection value\n")
            continue

        if (selection == 1):
            TV_gen()

        elif (selection == 2):
            # Used for file access
            script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in

            # Select circuit benchmark file, default is circuit.bench
            while True:
                cktFile = "c432.bench"
                print("\n Read circuit benchmark file: use " + cktFile + "?" + " Enter to accept or type filename: ")
                userInput = input()
                if userInput == "":
                    break
                else:
                    cktFile = os.path.join(script_dir, userInput)
                    if not os.path.isfile(cktFile):
                        print("File does not exist. \n")
                    else:
                        break
            circuit = netRead(cktFile)

            fault_out = "full_f_list.txt"
            fault_out = open(fault_out, "w")
            fault_out.write("# circuit.bench\n#fullSSA fault list\n\n")
            for f in circuit['FAULTS'][1]:
                fault_out.write(f + '\n')
            fault_out.write("\n#total faults: " + repr(len(circuit['FAULTS'][1])))
            fault_out.close()

            # keep an initial (unassigned any value) copy of the circuit for an easy reset
            newCircuit = circuit

            # saving the fault list
            flistName = "full_f_list.txt"
            # flist = read_flist(flistName)
            # # preserver = read_flist(flistName)
            # totalNumFaultsPossible = len(flist)

            while (True):
                user_batch = input("Choose a batch size in [1, 10]:")

                try:
                    batch = int(user_batch)
                except:
                    print("ERROR: Please type valid input -_- ..|.,\n")
                    continue

                if (batch > 10 or batch < 1):
                    print("ERROR: Invalid batch value\n")
                    continue
                else:
                    break

            # Select circuit benchmark file, default is circuit.bench
            print("input files: c432.bench, full_f_list.txt,  TV_A.txt, TV_B.txt, TV_C.txt,TV_D.txt, TV_E.txt" + \
                  "\noutput file: f_cvg.csv\n" + \
                  "\nProcessing...\n")

            TV_names = ["TV_A.txt", "TV_B.txt", "TV_C.txt", "TV_D.txt", "TV_E.txt"]
            fs_result = open("fault_sim_result.txt", "w+")
            fs_result.write("#input: " + cktFile + "\n")
            fs_result.write("#input: " + flistName + "\n")

            percent = open("percentages.txt", "w")
            #percent.write("Batch size is " + str(batch) + "\n")

            circFile = open(cktFile, "r")
            N = get_input_size(circFile)
            circFile.close()

            # Compute the overhead of N groupings of 8 for vector size
            N_overhead = (m.ceil(N / 8)) * 8

            for curr_tv_set in TV_names:
                fs_result.write("#input: " + curr_tv_set + "\n")
                fs_result.write("\n")

                percent.write(curr_tv_set + "\n")

                tv_list = TV_map[curr_tv_set]
                # Reset circuit before start
                resetCircuit(circuit)

                batch_fault_ctr = 0
                batch_result_accumulator = 0
                limiter = 0
                tvNumber = 0

                # initializing list to add faults found
                faults_Found = []

                flist = read_flist(flistName)
                totalNumFaultsPossible = len(flist)

                for line in tv_list:
                    if limiter == MAX_BATCH:
                        break

                    print("\n ---> Now ready to simulate INPUT = " + line[N_overhead - N:])
                    circuit = inputRead(circuit, line[N_overhead - N:])

                    # Empty the "good" output value for each TV
                    output = ""
                    tvNumber += 1
                    faults_count = 0

                    if circuit == -1:
                        print("INPUT ERROR: INSUFFICIENT BITS")
                        # After each input line is finished, reset the netList
                        circuit = newCircuit
                        print("...move on to next input\n")
                        continue
                    elif circuit == -2:
                        print("INPUT ERROR: INVALID INPUT VALUE/S")
                        # After each input line is finished, reset the netList
                        circuit = newCircuit
                        print("...move on to next input\n")
                        continue

                    # simulate no faults circuit
                    circuit = basic_sim(circuit)

                    for y in circuit["OUTPUTS"][1]:
                        if not circuit[y][2]:
                            output = "NETLIST ERROR: OUTPUT LINE \"" + y + "\" NOT ACCESSED"
                            break
                        output = str(circuit[y][3]) + output
                        # breakpoint()

                    # After each input line is finished, reset the circuit
                    resetCircuit(circuit)

                    ########################################################
                    # detectedFaultsforCurrentTV will be updated with all the detected SA faults in the current TV.
                    current_TV_Detected_Faults = sa_Fault_Simulator(flist, circuit, line[N_overhead - N:], newCircuit,
                                                                    output)
                    fs_result.write("\ntv" + str(tvNumber) + " = " + line[N_overhead - N:] + " -> " + str(
                        output) + " (good)\n")  # JEM
                    # getting length of first dimension of list JEM
                    lengthList = len(current_TV_Detected_Faults[0])
                    # iterating through list to print output of TV @ fault JEM
                    fs_result.write("detected:\n")
                    i = 0
                    print("length of list: " + str(lengthList) + "\n")

                    while i < lengthList:
                        fs_result.write(current_TV_Detected_Faults[0][i] + ":  " + line[N_overhead - N:] + " -> " +
                                        current_TV_Detected_Faults[1][i] + "\n")

                        if (current_TV_Detected_Faults[0][i] not in faults_Found):
                            # add to faults_Found JEM DEBUG
                            faults_Found.append(current_TV_Detected_Faults[0][i])
                            faults_count += 1

                        i += 1

                    if (batch_fault_ctr < batch):
                        batch_fault_ctr += 1
                        batch_result_accumulator += faults_count
                    # breakpoint()
                    if (batch_fault_ctr == batch):
                        percent.write(str(m.ceil((batch_result_accumulator / totalNumFaultsPossible) * 100)) + "\n")
                        batch_fault_ctr = 0
                        limiter += 1
                        # breakpoint()
                        print(limiter)

                    # After each input line is finished, reset the circuit
                    # print("\n *** Now resetting circuit back to unknowns... \n")
                    resetCircuit(circuit)
                    print("\n*******************\n")

                # JEM printing summary of faults found
                # delete flist as u find faults/add to faults_Found
                for i in faults_Found:
                    if (i in flist):
                        # add to faults_Found JEM DEBUG
                        flist.remove(i)
                undetectedFaults = len(flist)
                total_faults_found = len(faults_Found)

                # make list of undetected faults JEM
                fs_result.write("\n\ntotal detected faults: " + str(total_faults_found) + "\n")
                fs_result.write("\n\nundetected faults: " + str(undetectedFaults) + "\n")

                for undetected_fault in flist:
                    fs_result.write('%s\n' % undetected_fault)

                # print fault list JEM DEBUG
                percentFaultsFound = 100 * float(total_faults_found) / float(totalNumFaultsPossible)
                fs_result.write(
                    "\n\nfault coverage: " + str(total_faults_found) + "/" + str(totalNumFaultsPossible) + " = " + str(
                        percentFaultsFound) + "% \n")  # JEM

                # flist = preserver
            # closing fault sim result file
            percent.close()
            fs_result.close()
            print("Done.")

        elif (selection == 3):
            print("(*Just give us extra credit, pls :)*) ")

        elif (selection == 4):
            Project4();

        elif (selection == 5):
            break

    csvFile = open("f_cvg_c432_b10s.csv", "w")

    tvA = []
    tvB = []
    tvC = []
    tvD = []
    tvE = []
    csvFile.write("TV#,A,B,C,D,E,Batch Size""\n")
    current = ""
    p = open("percentages.txt", "r")
    for line in p:
        if line == "\n" or line == " ":
            continue
        if line == "TV_A.txt\n":
            current = "A"
            line = next(p)
        elif line == "TV_B.txt\n":
            current = "B"
            line = next(p)
        elif line == "TV_C.txt\n":
            current = "C"
            line = next(p)
        elif line == "TV_D.txt\n":
            current = "D"
            line = next(p)
        elif line == "TV_E.txt\n":
            current = "E"
            line = next(p)

        line = line.replace("\n", "")
        line = line.replace(" ", "")

        if current == "A":
            tvA.append(line)
        elif current == "B":
            tvB.append(line)
        elif current == "C":
            tvC.append(line)
        elif current == "D":
            tvD.append(line)
        elif current == "E":
            tvE.append(line)
    cxt = batch
    for i in range(0, len(tvA)):
        csvFile.write(str(i + 1) + "," + tvA[i] + "," + tvB[i] + "," + tvC[i] + "," + tvD[i] + "," + tvE[i] + "," + str(
            cxt) + "\n")
        cxt = cxt + batch
    csvFile.close()

if __name__ == "__main__":
    main()