# Create and activate anaconda environment
conda create -n build_polyaxon_libraries

source activate build_polyaxon_libraries

# Install conda-build and anaconda-client
conda install conda-build -y
conda install anaconda-client -y

# You must type your anaconda credentials
anaconda login

# Building conda packages

array=( 2.7 3.6 3.7 )
platforms=( osx-64 linux-32 linux-64 win-32 win-64 )

for python_version in "${array[@]}"
do
        echo "Python version: " $python_version

	# Remove build directory
	rm -rf build/
        rm -rf $CONDA_PREFIX/conda-bld

	# Workaround to ignore numpy
	mkdir -p build/numpy

	# Libraries with specific versions
	conda skeleton pypi rhea --version 0.4.5 --output-dir build/ --python $python_version
	conda skeleton pypi raven --version 6.7.0 --output-dir build/ --python $python_version

	# Polyaxon CLI
	conda skeleton pypi polyaxon-cli --recursive --output-dir build/ --python $python_version
	conda build build/polyaxon-cli/meta.yaml --no-test --python $python_version

	# Remove repo-data files
	rm $CONDA_PREFIX/conda-bld/linux-64/repodata*

	find $CONDA_PREFIX/conda-bld/linux-64/ -name *.tar.bz2 | while read file
	do
	    echo $file
	    for platform in "${platforms[@]}"
	    do
	       conda convert --platform $platform $file  -o $CONDA_PREFIX/conda-bld/
	    done

	done
	
        # Upload
	find $CONDA_PREFIX/conda-bld/ -name *.tar.bz2 | while read file
	do
	    echo "Uploading... " $file
            anaconda upload $file
        done

	# Remove build directory
	rm -rf build/
        rm -rf $CONDA_PREFIX/conda-bld
done

# Deactivate and Remove Conda Environment
conda deactivate
conda env remove -n build_polyaxon_libraries

