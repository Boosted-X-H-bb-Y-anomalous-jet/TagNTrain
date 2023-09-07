#!/bin/bash
echo "H5 conversion script starting"
source /cvmfs/cms.cern.ch/cmsset_default.sh
xrdcp root://cmseos.fnal.gov//store/user/mchitoto/H5_env.tgz ./
export SCRAM_ARCH=slc7_amd64_gcc820
scramv1 project CMSSW CMSSW_11_1_4
tar -xzvf H5_env.tgz
rm H5_env.tgz

mkdir tardir; cp tarball.tgz tardir/; cd tardir/
tar -xzf tarball.tgz; rm tarball.tgz
cp -r * ../CMSSW_11_1_4/src/CASEUtils/H5_maker/; cd ../CMSSW_11_1_4/src/CASEUtils/H5_maker/
echo "IN RELEASE"
pwd
ls
eval `scramv1 runtime -sh`

echo python run_h5_condor.py
python run_h5_condor.py

xrdcp -f *.csv root://cmseos.fnal.gov//store/user/mchitoto/H5_output/
