#!/usr/bin/env python
from __future__ import division, print_function
import sys, Image, argparse, os, glob

## change these variables to configure the defaults for the script
D_SIMILARITY_THRESHOLD = 90  # default minimum similarity % required to be added to the output; 90% is a better baseline if looking for resizes/full dupes only

def avg(values):
    if type(values) in (type(1), type(1.0)):
        return values
    return sum(values)/len(values)

def hamming_distance(a_list, b_list):
    return sum(item1 != item2 for item1, item2 in zip(a_list, b_list))

def num_pairs(num_items):
    num_pairs = 0
    while num_items > 0:
        num_items -= 1
        num_pairs += num_items
    return num_pairs

parser = argparse.ArgumentParser(description="Check for duplicate images, by comparing using simple perceptual hashes.")
parser.add_argument("files", metavar="file", type=str, nargs="*",
        help="a file for comparison (non-image files will be automatically discarded)")
parser.add_argument("-r", "--recursive-check", action="store_true",
        help="recurse into directories below the current one")
parser.add_argument("-q", "--quiet", action="store_false", dest="verbose",
        help="don't output hashing/comparison statuses")
parser.add_argument("-v", "--verbose", action="store_true", dest="verbose",
        help="output hashing/comparison statuses")
parser.add_argument("-t", "--similarity-threshold", "--threshold", metavar="T", type=int,
        help="minimum percentage similarity necessary to be listed in output", default=D_SIMILARITY_THRESHOLD)
parser.add_argument("-o", "--out-html-file", metavar="htmlfile", type=str, dest="out_file",
        help="file to write HTML-formatted output to (will not write HTML output if no filename given, or no results)", default="")

args = parser.parse_args()

if len(args.files) == 0:
    items = glob.glob("*")
else:
    items = args.files

pics = []
for item in items:
    if args.recursive_check and os.path.isdir(item):
        for root, dirs, files in os.walk(item):
            full_fname = lambda fname : os.path.join(root, fname)
            pics.extend(list(map(full_fname, files)))
    elif os.path.isfile(item):
        pics.append(item)

img_hashes = []
num_pics = len(pics)  # stored separately so we can decrease it on non-images
pic_index = 0
for pic in pics:
    try:
        im = Image.open(pic)
    except IOError:
        sys.stderr.write("Failed to open {0} as image.\n".format(pic))
        num_pics -= 1
    else:
        im = im.resize((8, 8), Image.BILINEAR)
        grayscale_pixels = list(map(avg, list(im.getdata())))
        del im
        pixel_avg = avg(grayscale_pixels)
        img_hashes.append((pic, [(pixel > pixel_avg) for pixel in grayscale_pixels]))
        pic_index += 1
        if args.verbose:
            print("Hashed {0}/{1}(?) images.".format(pic_index, num_pics))

similar = {}
pair_index = 0
total_pairs = num_pairs(len(img_hashes))
for a_index in xrange(len(img_hashes)):
    for b_index in xrange(a_index+1, len(img_hashes)):
        a, b = img_hashes[a_index], img_hashes[b_index]
        diff = ((64 - hamming_distance(a[1], b[1]))*100)//64
        if diff >= args.similarity_threshold:
            similar[(a[0], b[0])] = diff
        pair_index += 1
        if args.verbose:
            print("Compared {0}/{1} pairs.".format(pair_index, total_pairs))

if args.verbose:
    print("Done!\n")

if args.out_file != "" and len(similar) > 0:
    results_file = open(args.out_file, "w")
    results_file.write("<html><head><title>Similar images</title></head><body>")
else:
    results_file = None

for pair in similar:
    print("{0}\t{1}\t{2}% similar".format(pair[0], pair[1], similar[pair]))
    if results_file is not None:
        results_file.write("<h2>{2}% similar</h2><table><tr><td><img src=\"{0}\"></td><td><img src=\"{1}\"></td></tr><tr><td>{0}</td><td>{1}</td></tr></table>".format(pair[0], pair[1], similar[pair]))

if results_file is not None:
    results_file.write("</body></html>")
    results_file.close()
    print("\nAlso wrote HTML-formatted results to {0}".format(args.out_file))
