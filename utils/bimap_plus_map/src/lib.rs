use bimap::{BiMap, Overwritten};
use std::collections::hash_map::Iter;
use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct BiMapPlusMap<L, R, V>
where
    L: std::fmt::Debug + Eq + Hash,
    R: std::fmt::Debug + Eq + Hash,
{
    bimap: BiMap<L, R>,
    hashmap: HashMap<L, V>,
}

use bimap::hash::{LeftValues, RightValues};
use std::hash::Hash;

impl<L, R, V> BiMapPlusMap<L, R, V>
where
    L: std::fmt::Debug + Eq + Hash + Clone,
    R: std::fmt::Debug + Eq + Hash,
{
    pub fn new() -> Self {
        Self::default()
    }

    pub fn insert(&mut self, left: L, right: R, value: V) {
        match self.bimap.insert(left.clone(), right) {
            Overwritten::Neither | Overwritten::Left(_, _) | Overwritten::Pair(_, _) => {
                self.hashmap.insert(left, value);
            }
            Overwritten::Right(l1, _) => {
                self.hashmap.remove(&l1);
                self.hashmap.insert(left, value);
            }
            Overwritten::Both((l1, _), (l2, _)) => {
                self.hashmap.remove(&l1);
                self.hashmap.remove(&l2);
                self.hashmap.insert(left, value);
            }
        }
    }

    pub fn left_keys_iter(&self) -> LeftValues<'_, L, R> {
        self.bimap.left_values()
    }

    pub fn right_keys_iter(&self) -> RightValues<'_, L, R> {
        self.bimap.right_values()
    }

    pub fn left_items_iter(&self) -> Iter<'_, L, V> {
        self.hashmap.iter()
    }

    pub fn bimap_get_by_left(&self, left: &L) -> Option<&R> {
        self.bimap.get_by_left(left)
    }

    pub fn bimap_get_by_right(&self, right: &R) -> Option<&L> {
        self.bimap.get_by_right(right)
    }

    pub fn hashmap_get_by_left(&self, left: &L) -> Option<&V> {
        self.hashmap.get(left)
    }

    pub fn hashmap_get_by_right(&self, right: &R) -> Option<&V> {
        let left = self.bimap_get_by_right(right)?;
        self.hashmap.get(left)
    }

    pub fn hashmap_get_mut_by_left(&mut self, left: &L) -> Option<&mut V> {
        self.hashmap.get_mut(left)
    }

    pub fn hashmap_get_mut_by_right(&mut self, right: &R) -> Option<&mut V> {
        let left = self.bimap.get_by_right(right)?;
        self.hashmap.get_mut(left)
    }

    pub fn remove_by_left(&mut self, left: &L) -> Option<V> {
        let val = self.hashmap.remove(left);
        self.bimap.remove_by_left(left);
        val
    }

    pub fn remove_by_right(&mut self, right: &R) -> Option<V> {
        if let Some(left) = self.bimap.get_by_right(right) {
            let val = self.hashmap.remove(left);
            self.bimap.remove_by_right(right);
            val
        } else {
            None
        }
    }
}

impl<L, R, V> Default for BiMapPlusMap<L, R, V>
where
    L: std::fmt::Debug + Eq + Hash + Clone,
    R: std::fmt::Debug + Eq + Hash,
{
    fn default() -> Self {
        BiMapPlusMap {
            bimap: BiMap::new(),
            hashmap: HashMap::new(),
        }
    }
}
