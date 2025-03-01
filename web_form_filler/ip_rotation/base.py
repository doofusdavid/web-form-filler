"""
Base IP Rotator - Abstract base class for IP rotation strategies.
"""

from abc import ABC, abstractmethod

class BaseIPRotator(ABC):
    """Abstract base class for IP rotation strategies."""
    
    @abstractmethod
    def apply_to_session(self, session):
        """Apply IP rotation to a requests session.
        
        Args:
            session (requests.Session): The session to apply IP rotation to.
            
        Returns:
            requests.Session: The modified session.
        """
        pass
    
    def rotate_ip(self):
        """Rotate to a new IP address.
        
        This method is optional and may be implemented by subclasses
        that support active IP rotation.
        """
        pass