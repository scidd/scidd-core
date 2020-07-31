
import pytest
import requests

from sciid import SciID

# sci_id, url
expected_results_galex_sciid_to_url = [

	# gr6
	("sciid:/astro/file/galex/gr6/MISDR1_24340_0267_0001-fd-movie.fits",
	 "http://galex.stsci.edu/data/GR6/pipe/01-vsn/03011-MISDR1_24340_0267/d/00-visits/0001-img/07-try/MISDR1_24340_0267_0001-fd-movie.fits.gz"),
	("sciid:/astro/file/galex/gr6/MISDR1_24339_0267_0002-fd-cat.fits",
	 "http://galex.stsci.edu/data/GR6/pipe/01-vsn/03010-MISDR1_24339_0267/d/00-visits/0002-img/07-try/MISDR1_24339_0267_0002-fd-cat.fits.gz"),
	("sciid:/astro/file/galex/gr6/MISDR1_24308_0267_0001-nd-cat.fits",
	 "http://galex.stsci.edu/data/GR6/pipe/01-vsn/03009-MISDR1_24308_0267/d/00-visits/0001-img/07-try/MISDR1_24308_0267_0001-nd-cat.fits.gz"),
	("sciid:/astro/file/galex/gr6/MISDR1_24307_0267-fd-int.fits",
	 "http://galex.stsci.edu/data/GR6/pipe/01-vsn/03008-MISDR1_24307_0267/d/01-main/0001-img/07-try/MISDR1_24307_0267-fd-int.fits.gz"),
	("sciid:/astro/file/galex/gr6/MISDR1_24279_0266-nd-skybg.fits",
	 "http://galex.stsci.edu/data/GR6/pipe/01-vsn/03001-MISDR1_24279_0266/d/01-main/0001-img/07-try/MISDR1_24279_0266-nd-skybg.fits.gz"),
	("sciid:/astro/file/galex/gr6/NGA_NGC0024_0001-fd-exp.fits",
	 "http://galex.stsci.edu/data/GR6/pipe/01-vsn/05002-NGA_NGC0024/d/00-visits/0001-img/07-try/NGA_NGC0024_0001-fd-exp.fits.gz"),
	("sciid:/astro/file/galex/gr6/SIRTFFL_10_0011-nd-skybg.fits",
	 "http://galex.stsci.edu/data/GR6/pipe/01-vsn/06772-SIRTFFL_10/d/00-visits/0011-img/07-try/SIRTFFL_10_0011-nd-skybg.fits.gz"),
	("sciid:/astro/file/galex/gr6/NGA_Cartwheel-nd-objmask.fits",
	 "http://galex.stsci.edu/data/GR6/pipe/01-vsn/05005-NGA_Cartwheel/d/01-main/0001-img/07-try/NGA_Cartwheel-nd-objmask.fits.gz"),
	 # gr6
	("sciid:/astro/file/galex/gr7/MISGCSN1_12790_0234o-xd-mcat.fits",
	 "http://galex.stsci.edu/data/GR7/pipe/01-vsn/18293-MISGCSN1_12790_0234o/d/01-main/0007-img/07-try/MISGCSN1_12790_0234o-xd-mcat.fits.gz"),
	("sciid:/astro/file/galex/gr7/WDST_J2317m0016_css34203-nd-rr.fits",
	 "http://galex.stsci.edu/data/GR7/pipe/02-vsn/53280-WDST_J2317m0016_css34203/d/01-main/0001-img/07-try/WDST_J2317m0016_css34203-nd-rr.fits.gz"),
	("sciid:/astro/file/galex/gr7/MIS2DFR_40835_0823-xd-mcat.fits",
	 "http://galex.stsci.edu/data/GR7/pipe/01-vsn/04043-MIS2DFR_40835_0823/d/01-main/0007-img/07-try/MIS2DFR_40835_0823-xd-mcat.fits.gz"),
	("sciid:/astro/file/galex/gr7/MIS2DFR_41085_0812_0006-aspraw.fits",
	 "http://galex.stsci.edu/data/GR7/pipe/01-vsn/04017-MIS2DFR_41085_0812/d/00-visits/0006-img/07-try/MIS2DFR_41085_0812_0006-aspraw.fits.gz"),
	("sciid:/astro/file/galex/gr7/MISDR1_20625_0641_0002-nd-intbgsub.fits",
	 "http://galex.stsci.edu/data/GR7/pipe/01-vsn/03659-MISDR1_20625_0641/d/00-visits/0002-img/07-try/MISDR1_20625_0641_0002-nd-intbgsub.fits.gz"),
	("sciid:/astro/file/galex/gr7/MISDR1_11257_0633-nd-rrhr.fits",
	 "http://galex.stsci.edu/data/GR7/pipe/01-vsn/03632-MISDR1_11257_0633/d/01-main/0007-img/07-try/MISDR1_11257_0633-nd-rrhr.fits.gz"),
	("sciid:/astro/file/galex/gr7/PTF10cwr-nd-rrhr.fits",
	 "http://galex.stsci.edu/data/GR7/pipe/01-vsn/05668-PTF10cwr/d/01-main/0007-img/07-try/PTF10cwr-nd-rrhr.fits.gz"),
	("sciid:/astro/file/galex/gr7/PTF10cwr-nd-rrhr.fits",
	 "http://galex.stsci.edu/data/GR7/pipe/01-vsn/05668-PTF10cwr/d/01-main/0007-img/07-try/PTF10cwr-nd-rrhr.fits.gz")
]


@pytest.mark.parametrize("sci_id, url", expected_results_galex_sciid_to_url)
def test_galex_resolve_filenames(sci_id, url):
	'''
	Test resolving GALEX SciID filenames to URL.
	'''
	
	assert SciID(sci_id).url == url

	# check resource exists	
	r = requests.head(url)
	assert r.status_code == requests.codes.ok
