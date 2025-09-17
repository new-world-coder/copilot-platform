"""
DOM observation utilities for the Copilot Platform
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DOMObserver:
    """Observe and track DOM changes"""
    
    def __init__(self):
        self.observers = {}
        self.change_callbacks = []
        self.is_observing = False
    
    def start_observing(self, target_element: Optional[str] = None):
        """Start observing DOM changes"""
        if self.is_observing:
            return
        
        try:
            # Use MutationObserver to watch for changes
            observer = MutationObserver(self._handle_mutation)
            
            # Configure what to observe
            config = {
                'childList': True,
                'subtree': True,
                'attributes': True,
                'attributeOldValue': True,
                'characterData': True,
                'characterDataOldValue': True
            }
            
            # Start observing
            if target_element:
                element = document.querySelector(target_element)
                if element:
                    observer.observe(element, config)
                else:
                    logger.warning(f"Target element {target_element} not found")
            else:
                observer.observe(document.body, config)
            
            self.observers['main'] = observer
            self.is_observing = True
            
            logger.info("DOM observation started")
            
        except Exception as e:
            logger.error(f"Error starting DOM observation: {e}")
    
    def stop_observing(self):
        """Stop observing DOM changes"""
        for observer in self.observers.values():
            observer.disconnect()
        
        self.observers.clear()
        self.is_observing = False
        
        logger.info("DOM observation stopped")
    
    def _handle_mutation(self, mutations):
        """Handle DOM mutations"""
        for mutation in mutations:
            change_data = {
                'type': mutation.type,
                'target': mutation.target,
                'timestamp': datetime.utcnow().isoformat(),
                'added_nodes': [],
                'removed_nodes': [],
                'attribute_changes': []
            }
            
            # Handle added nodes
            for node in mutation.addedNodes:
                if node.nodeType === Node.ELEMENT_NODE:
                    change_data['added_nodes'].append({
                        'tag': node.tagName,
                        'id': node.id,
                        'class': node.className,
                        'text': node.textContent[:100] if node.textContent else ''
                    })
            
            # Handle removed nodes
            for node in mutation.removedNodes:
                if node.nodeType === Node.ELEMENT_NODE:
                    change_data['removed_nodes'].append({
                        'tag': node.tagName,
                        'id': node.id,
                        'class': node.className,
                        'text': node.textContent[:100] if node.textContent else ''
                    })
            
            # Handle attribute changes
            if mutation.type === 'attributes':
                change_data['attribute_changes'].append({
                    'attribute': mutation.attributeName,
                    'old_value': mutation.oldValue,
                    'new_value': mutation.target.getAttribute(mutation.attributeName)
                })
            
            # Notify callbacks
            for callback in self.change_callbacks:
                try:
                    callback(change_data)
                except Exception as e:
                    logger.error(f"Error in change callback: {e}")
    
    def add_change_callback(self, callback: Callable):
        """Add a callback for DOM changes"""
        self.change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: Callable):
        """Remove a change callback"""
        if callback in self.change_callbacks:
            self.change_callbacks.remove(callback)


class ElementTracker:
    """Track specific elements on the page"""
    
    def __init__(self):
        self.tracked_elements = {}
        self.observer = DOMObserver()
    
    def track_element(self, selector: str, callback: Callable):
        """Track a specific element"""
        try:
            element = document.querySelector(selector)
            if not element:
                logger.warning(f"Element {selector} not found")
                return
            
            # Store tracking info
            self.tracked_elements[selector] = {
                'element': element,
                'callback': callback,
                'last_state': self._get_element_state(element)
            }
            
            # Start observing if not already
            if not self.observer.is_observing:
                self.observer.start_observing()
            
            # Add callback for changes
            self.observer.add_change_callback(self._handle_element_change)
            
            logger.info(f"Started tracking element: {selector}")
            
        except Exception as e:
            logger.error(f"Error tracking element {selector}: {e}")
    
    def stop_tracking_element(self, selector: str):
        """Stop tracking a specific element"""
        if selector in self.tracked_elements:
            del self.tracked_elements[selector]
            logger.info(f"Stopped tracking element: {selector}")
    
    def _get_element_state(self, element):
        """Get current state of an element"""
        return {
            'text': element.textContent,
            'html': element.innerHTML,
            'attributes': dict(element.attributes),
            'position': element.getBoundingClientRect(),
            'visible': self._is_element_visible(element)
        }
    
    def _is_element_visible(self, element):
        """Check if element is visible"""
        rect = element.getBoundingClientRect()
        return rect.width > 0 and rect.height > 0
    
    def _handle_element_change(self, change_data):
        """Handle changes to tracked elements"""
        for selector, tracking_info in self.tracked_elements.items():
            element = tracking_info['element']
            
            # Check if this change affects our tracked element
            if self._change_affects_element(change_data, element):
                new_state = self._get_element_state(element)
                old_state = tracking_info['last_state']
                
                # Detect what changed
                changes = self._detect_changes(old_state, new_state)
                
                if changes:
                    try:
                        tracking_info['callback'](changes, new_state, old_state)
                    except Exception as e:
                        logger.error(f"Error in element change callback: {e}")
                    
                    # Update last state
                    tracking_info['last_state'] = new_state
    
    def _change_affects_element(self, change_data, element):
        """Check if a change affects a specific element"""
        # Check if the element itself changed
        if change_data['target'] === element:
            return True
        
        # Check if any added/removed nodes are children of our element
        for node_data in change_data['added_nodes'] + change_data['removed_nodes']:
            if element.contains(node_data.get('element')):
                return True
        
        return False
    
    def _detect_changes(self, old_state, new_state):
        """Detect what changed between states"""
        changes = {}
        
        if old_state['text'] !== new_state['text']:
            changes['text'] = {
                'old': old_state['text'],
                'new': new_state['text']
            }
        
        if old_state['html'] !== new_state['html']:
            changes['html'] = {
                'old': old_state['html'],
                'new': new_state['html']
            }
        
        if old_state['attributes'] !== new_state['attributes']:
            changes['attributes'] = {
                'old': old_state['attributes'],
                'new': new_state['attributes']
            }
        
        if old_state['visible'] !== new_state['visible']:
            changes['visibility'] = {
                'old': old_state['visible'],
                'new': new_state['visible']
            }
        
        return changes


class FormObserver:
    """Observe form interactions"""
    
    def __init__(self):
        self.form_callbacks = []
        self.input_callbacks = []
    
    def start_observing_forms(self):
        """Start observing form interactions"""
        # Observe form submissions
        document.addEventListener('submit', self._handle_form_submit)
        
        # Observe input changes
        document.addEventListener('input', self._handle_input_change)
        document.addEventListener('change', self._handle_input_change)
        
        logger.info("Form observation started")
    
    def stop_observing_forms(self):
        """Stop observing form interactions"""
        document.removeEventListener('submit', self._handle_form_submit)
        document.removeEventListener('input', self._handle_input_change)
        document.removeEventListener('change', self._handle_input_change)
        
        logger.info("Form observation stopped")
    
    def add_form_callback(self, callback: Callable):
        """Add callback for form submissions"""
        self.form_callbacks.append(callback)
    
    def add_input_callback(self, callback: Callable):
        """Add callback for input changes"""
        self.input_callbacks.append(callback)
    
    def _handle_form_submit(self, event):
        """Handle form submission"""
        form_data = self._extract_form_data(event.target)
        
        for callback in self.form_callbacks:
            try:
                callback(form_data, event)
            except Exception as e:
                logger.error(f"Error in form callback: {e}")
    
    def _handle_input_change(self, event):
        """Handle input changes"""
        input_data = {
            'name': event.target.name,
            'type': event.target.type,
            'value': event.target.value,
            'id': event.target.id,
            'class': event.target.className
        }
        
        for callback in self.input_callbacks:
            try:
                callback(input_data, event)
            except Exception as e:
                logger.error(f"Error in input callback: {e}")
    
    def _extract_form_data(self, form):
        """Extract data from form"""
        form_data = {}
        
        for element in form.elements:
            if element.name:
                if element.type === 'checkbox':
                    form_data[element.name] = element.checked
                elif element.type === 'radio':
                    if element.checked:
                        form_data[element.name] = element.value
                else:
                    form_data[element.name] = element.value
        
        return form_data


# Global instances for easy access
dom_observer = DOMObserver()
element_tracker = ElementTracker()
form_observer = FormObserver()
