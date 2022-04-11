# Converts language reactor subtitles to SRT
import argparse
import datetime
from datetime import timedelta

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-inp",type=str, help = "Path to main data directory (not specific quantifier)", default ="./subs.txt")
    parser.add_argument("-out_en",type=str, help = "Path to store outputs", default ="./out_en.srt")
    parser.add_argument("-out_cn",type=str, help = "Path to store outputs", default ="./out_cn.srt")
    parser.add_argument("-offset",type=int, help = "Offset seconds of starting the subtitle", default = 0)
    args = parser.parse_args()
    return args

def get_start_time(curr_line):
    """
    Input: A list of strings representing a line in the txt file in format [Time, Chinese, English]
    Return: A tuple, element 0 = list of each value as an int,  element 1 = string of the start time for an SRT line in format HR:MN:SE,MIL
    """

    # Put time into format [HRS, MINS, SECS, MILLISECS], each element is an int
    time_split = curr_line[0].split(":")

    # Make sure list is of size 4
    while len(time_split) < 3:
        time_split.insert(0, "0")

    # Remove any "s"
    for i in range(len(time_split)):
        time_split[i] = time_split[i].replace("s", "")

    # If any values below 10, put zero in front
    for i in range(len(time_split)):
        if int(time_split[i]) < 10:
            time_split[i] = "0" + str(int(time_split[i]))

    # Milliseconds always 000
    time_split.append("000")

    time_string = time_split[0] + ":" + time_split[1] + ":" + time_split[2] + "," + time_split[3]
    time_int_list = [int(time_split[0]), int(time_split[1]), int(time_split[2]), int(time_split[3])]

    return (time_int_list, time_string)
    

def get_end_time(stime_curr, stime_next):
    """
    Input: Two tuples of format ([HRS, MINS, SECS, MILSECS], HRS:MINS:SECS,MILISECS)
    Output: A tuple of same format with end time of current line
    """

    # Convert stime_next to python datetime
    stime_next_dt = datetime.time(stime_next[0][0], stime_next[0][1], stime_next[0][2], stime_next[0][3])
    
    # End time of curr is stime_next - 500 milliseconds
    etime_curr_dt = (datetime.datetime.combine(datetime.date(1,1,1),stime_next_dt) + timedelta(milliseconds = -500)).time()
    etime_curr_int = [etime_curr_dt.hour, etime_curr_dt.minute, etime_curr_dt.second, int(etime_curr_dt.microsecond/1000)]
    etime_curr_string = [str(etime_curr_int[0]), str(etime_curr_int[1]), str(etime_curr_int[2]), str(etime_curr_int[3])]
    
    # If any values below 10, put zero in front
    for i in range(len(etime_curr_string)):
        if int(etime_curr_string[i]) < 10:
            etime_curr_string[i] = "0" + etime_curr_string[i]

    etime_curr_string = str(etime_curr_string[0]) + ":" + str(etime_curr_string[1]) + ":" + str(etime_curr_string[2]) + "," + str(etime_curr_string[3])
    
    return (etime_curr_int, etime_curr_string)


if __name__ == "__main__":

    args = parse_args()

    with open(args.inp, encoding="utf-8") as f, open(args.out_cn, "w", encoding="utf-8") as f2, open(args.out_en, "w", encoding="utf-8") as f3:
        
        data = f.read()

        lines = []

        # Get initial strings from file
        strings = data.split("\n")
        for s in strings:
            x = s.split("\t")
            lines.append(x)

        # For each line, convert into a final SRT string
        for i in range(len(lines)):
            line = lines[i]
            if i + 1 < len(lines):
                next_line = lines[i+1]
            else:
                stime_curr = get_start_time(line)
                line[0] = stime_curr[1] + " --> " + stime_curr[1].replace(",000", ",500")
                break


            # Get beginning time for current line
            stime_curr = get_start_time(line)
            stime_next = get_start_time(next_line)

            # Get end time for current line
            etime_curr = get_end_time(stime_curr, stime_next)

            
            # Final format of line time
            line[0] = stime_curr[1] + " --> " + etime_curr[1]

        #  Write SRT strings to file
        for i, line in enumerate(lines):
            cn_line = str((i+1)) + "\n" + line[0] + " " + "\n" + line[1]
            en_line = str((i+1)) + "\n" + line[0] + " " + "\n" + line[2]
            f2.write(cn_line + "\n\n")
            f3.write(en_line + "\n\n")
            
            