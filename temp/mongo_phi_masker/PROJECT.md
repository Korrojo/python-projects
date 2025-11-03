# MongoDB PHI Masker

## Table of Contents
- [Project Overview](#project-overview)
- [Features](#features)
- [Getting Started](#getting-started)
- [Project Status](#project-status)
- [Roadmap](#roadmap)

## Project Overview

A comprehensive data pipeline for extracting data from MongoDB, masking Protected Health Information (PHI), and restoring it to another MongoDB collection.

## Features

- **Flexible Data Masking**: Mask PHI data in MongoDB collections using configurable rules
- **Complex Document Support**: Handle nested documents, arrays, and complex MongoDB structures
- **Incremental Processing**: Support for incremental data processing with checkpointing
- **Multi-environment Support**: Configuration for development, testing, and production environments
- **Performance Optimized**: Batch processing and multi-worker support for high-volume data
- **Dask Integration**: Parallel processing with configurable worker settings
- **In-situ Processing**: Mask documents directly in the source collection
- **Multiple Collection Support**: Process multiple collections in one run
- **Comprehensive Logging**: Detailed logging for auditing and troubleshooting
- **Error Handling**: Robust error handling and recovery mechanisms
- **Email Alerts**: Notification system for process completion and errors
- **Metrics Collection**: Performance and processing metrics collection
- **Docker Support**: Containerization for easy deployment
- **Kubernetes Ready**: Kubernetes manifests for production deployment
- **Backward Compatibility**: Support for both old and new APIs through compatibility layer

## Getting Started

### Prerequisites
- Python 3.8+
- MongoDB 4.4+
- Docker (optional)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mongophimasker.git
   cd mongophimasker
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Project Status

### Current Status
- ✅ Integration tests fixed and passing in Docker environment
- ✅ Validator improved with robust type checking
- ✅ Basic collections successfully processed and validated
- 🔄 Need to process 200+ remaining collections
- 🔄 Need to track progress and performance metrics

## Roadmap

### Version 1.1 (Current)
- [x] Clean up working branch
- [x] Create feature branch `feature/fax-field-masking`
- [x] Run unit tests before each commit
- [x] Run integration tests after major changes
- [ ] Verify test coverage
- [x] Add new tests for fax field masking
- [ ] Schedule periodic full test suite runs

### Future Enhancements
1. **Performance Optimization**
   - Implement batch processing for large collections
   - Add parallel processing capabilities
   - Optimize memory usage

2. **New Features**
   - Support for additional data types
   - Enhanced reporting capabilities
   - Web-based dashboard for monitoring

3. **Documentation**
   - Complete API documentation
   - Add more usage examples
   - Create video tutorials

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
