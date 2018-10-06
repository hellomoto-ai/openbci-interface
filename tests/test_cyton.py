from openbci_interface import cyton


def test_attributes():
    """Cyton board has 8 EEG channels and 3 AUX channels"""
    assert cyton.Cyton.num_eeg == 8
    assert cyton.Cyton.num_aux == 3
