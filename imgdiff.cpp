/*#include <iostream>
#include <png++/png.hpp>

int main(int argc, char* argv[]) {
    // Check the number of command-line arguments
    if (argc != 4) {
        std::cerr << "Usage: " << argv[0] << " <image1> <image2> <output>" << std::endl;
        return 1;
    }

    // Parse the command-line arguments
    const char* image1_filename = argv[1];
    const char* image2_filename = argv[2];
    const char* output_filename = argv[3];

    // Load the two images
    png::image<png::rgb_pixel> image1(image1_filename);
    png::image<png::rgb_pixel> image2(image2_filename);

    // Create a new image for the difference
    png::image<png::rgb_pixel> diff(image1.get_width(), image1.get_height());

    // Calculate the absolute difference between the two images
    for (size_t y = 0; y < image1.get_height(); ++y) {
        for (size_t x = 0; x < image1.get_width(); ++x) {
            diff[y][x] = png::rgb_pixel(
                std::abs(image2[y][x].red - image1[y][x].red),
                std::abs(image2[y][x].green - image1[y][x].green),
                std::abs(image2[y][x].blue - image1[y][x].blue)
            );
        }
    }

    // Save the difference image as a PNG file
    diff.write(output_filename);

    return 0;
}

#include <iostream>
#include <png++/png.hpp>
#include <thread>
#include <vector>

// Function to calculate the absolute difference between two tiles
void process_tile(
    const png::image<png::rgb_pixel>& image1,
    const png::image<png::rgb_pixel>& image2,
    png::image<png::rgb_pixel>& diff,
    size_t tile_x, size_t tile_y,
    size_t tile_width, size_t tile_height
) {
    // Calculate the absolute difference between the two tiles
    for (size_t y = tile_y; y < tile_y + tile_height; ++y) {
        for (size_t x = tile_x; x < tile_x + tile_width; ++x) {
            diff[y][x] = png::rgb_pixel(
                std::abs(image2[y][x].red - image1[y][x].red),
                std::abs(image2[y][x].green - image1[y][x].green),
                std::abs(image2[y][x].blue - image1[y][x].blue)
            );
        }
    }
}*/

#include <iostream>
#include <png++/png.hpp>
#include <thread>
#include <vector>

// Function to calculate the absolute difference between two tiles
void process_tile(
    const png::image<png::rgb_pixel>& image1,
    const png::image<png::rgb_pixel>& image2,
    png::image<png::rgb_pixel>& diff,
    size_t tile_x, size_t tile_y,
    size_t tile_width, size_t tile_height
) {
    // Calculate the absolute difference between the two tiles
    for (size_t y = tile_y; y < tile_y + tile_height; ++y) {
        for (size_t x = tile_x; x < tile_x + tile_width; ++x) {
            diff[y][x] = png::rgb_pixel(
                std::abs(image2[y][x].red - image1[y][x].red),
                std::abs(image2[y][x].green - image1[y][x].green),
                std::abs(image2[y][x].blue - image1[y][x].blue)
            );
        }
    }
}

int main(int argc, char* argv[]) {
    // Check the number of command-line arguments
    if (argc != 6) {
        std::cerr << "Usage: " << argv[0] << " <image1> <image2> <output> <tile_size> <num_threads>" << std::endl;
        return 1;
    }

    // Parse the command-line arguments
    const char* image1_filename = argv[1];
    const char* image2_filename = argv[2];
    const char* output_filename = argv[3];
    size_t tile_size = std::stoul(argv[4]);
    size_t num_threads = std::stoul(argv[5]);

    // Load the two images
    std::cout << "Image 1 loading\n";
    png::image<png::rgb_pixel> image1(image1_filename);
    std::cout << "Image 2 loading\n";
    png::image<png::rgb_pixel> image2(image2_filename);
    std::cout << "images loaded\n";

    // Create a new image for the difference
    png::image<png::rgb_pixel> diff(image1.get_width(), image1.get_height());

    // Calculate the number of tiles in each dimension
    size_t num_tiles_x = (image1.get_width() + tile_size - 1) / tile_size;
    size_t num_tiles_y = (image1.get_height() + tile_size - 1) / tile_size;

    // Create a vector to hold the threads
    std::vector<std::thread> threads;

    // Process each tile using multiple threads
    for (size_t i = 0; i < num_threads; ++i) {
        threads.emplace_back([&, i] {
            for (size_t tile_index = i; tile_index < num_tiles_x * num_tiles_y; tile_index += num_threads) {
                size_t tile_x = (tile_index % num_tiles_x) * tile_size;
                size_t tile_y = (tile_index / num_tiles_x) * tile_size;
                size_t tile_width = std::min(tile_size, image1.get_width() - tile_x);
                size_t tile_height = std::min(tile_size, image1.get_height() - tile_y);
                process_tile(image1, image2, diff, tile_x, tile_y, tile_width, tile_height);
            }
        });
    }

    // Wait for all threads to finish
    for (auto& thread : threads) {
        thread.join();
    }

    std::cout << "Image difference calculated\n";

    // Save the difference image as a PNG file
    diff.write(output_filename);

    std::cout << "output image file written\n";

    return 0;
}