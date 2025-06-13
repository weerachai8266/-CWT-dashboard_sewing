-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Generation Time: Jun 05, 2025 at 07:41 AM
-- Server version: 8.0.29
-- PHP Version: 8.2.2

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `automotive`
--

-- --------------------------------------------------------

--
-- Table structure for table `item`
--

CREATE TABLE `item` (
  `id` int NOT NULL,
  `item_number` varchar(50) NOT NULL,
  `product_name` varchar(255) NOT NULL,
  `configuration` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `color` varchar(100) DEFAULT NULL,
  `size` varchar(50) DEFAULT NULL,
  `style` varchar(100) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sewing_3rd`
--

CREATE TABLE `sewing_3rd` (
  `id` int NOT NULL,
  `item` varchar(255) NOT NULL,
  `qty` int NOT NULL DEFAULT '1',
  `status` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sewing_cap`
--

CREATE TABLE `sewing_cap` (
  `id` int NOT NULL,
  `fc` int NOT NULL,
  `fb` int NOT NULL,
  `rc` int NOT NULL,
  `rb` int NOT NULL,
  `3rd` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sewing_fb`
--

CREATE TABLE `sewing_fb` (
  `id` int NOT NULL,
  `item` varchar(255) NOT NULL,
  `qty` int NOT NULL DEFAULT '1',
  `status` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sewing_fc`
--

CREATE TABLE `sewing_fc` (
  `id` int NOT NULL,
  `item` varchar(255) NOT NULL,
  `qty` int NOT NULL DEFAULT '1',
  `status` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sewing_man`
--

CREATE TABLE `sewing_man` (
  `id` int NOT NULL,
  `fc` int NOT NULL,
  `fb` int NOT NULL,
  `rc` int NOT NULL,
  `rb` int NOT NULL,
  `3rd` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sewing_rb`
--

CREATE TABLE `sewing_rb` (
  `id` int NOT NULL,
  `item` varchar(255) NOT NULL,
  `qty` int NOT NULL DEFAULT '1',
  `status` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sewing_rc`
--

CREATE TABLE `sewing_rc` (
  `id` int NOT NULL,
  `item` varchar(255) NOT NULL,
  `qty` int NOT NULL DEFAULT '1',
  `status` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `item`
--
ALTER TABLE `item`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `item_number` (`item_number`);

--
-- Indexes for table `sewing_3rd`
--
ALTER TABLE `sewing_3rd`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sewing_cap`
--
ALTER TABLE `sewing_cap`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sewing_fb`
--
ALTER TABLE `sewing_fb`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sewing_fc`
--
ALTER TABLE `sewing_fc`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sewing_man`
--
ALTER TABLE `sewing_man`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sewing_rb`
--
ALTER TABLE `sewing_rb`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sewing_rc`
--
ALTER TABLE `sewing_rc`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `item`
--
ALTER TABLE `item`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sewing_3rd`
--
ALTER TABLE `sewing_3rd`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sewing_cap`
--
ALTER TABLE `sewing_cap`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sewing_fb`
--
ALTER TABLE `sewing_fb`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sewing_fc`
--
ALTER TABLE `sewing_fc`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sewing_man`
--
ALTER TABLE `sewing_man`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sewing_rb`
--
ALTER TABLE `sewing_rb`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sewing_rc`
--
ALTER TABLE `sewing_rc`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
