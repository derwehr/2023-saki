#!/bin/bash

# make sure we're in the right directory
cd "${0%/*}"/..

# Run tests
pytest
