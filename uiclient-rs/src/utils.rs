/// This function works like python's '%' operator on floats
pub fn fmod(a: f64, b: f64) -> f64 {
    ((a % b) + b) % b
}

/// This function works like python's '%' operator on ints
pub fn imod(a: i64, b: i64) -> i64 {
    ((a % b) + b) % b
}

// Tests
#[cfg(test)]
mod fmod_tests {
    #[test]
    fn test_fmod() {
        assert_eq!(0.0, super::fmod(0.0, 1.0));
        assert_eq!(0.0, super::fmod(1.0, 1.0));
        assert_eq!(1.0, super::fmod(1.0, 2.0));
        assert_eq!(0.5, super::fmod(2.5, 2.0));
        assert_eq!(1.5, super::fmod(-2.5, 2.0));
        assert_eq!(-0.5, super::fmod(-2.5, -2.0));
        assert_eq!(-1.5, super::fmod(2.5, -2.0));
        assert_eq!(0.5, super::fmod(2.0, 1.5));
        assert_eq!(1.0, super::fmod(-2.0, 1.5));
        assert!(super::fmod(1.0, 0.0).is_nan());
    }

    #[test]
    fn test_imod() {
        assert_eq!(0, super::imod(0, 1));
        assert_eq!(0, super::imod(1, 1));
        assert_eq!(1, super::imod(1, 10));
        assert_eq!(0, super::imod(10, 10));
        assert_eq!(0, super::imod(-10, 10));
        assert_eq!(9, super::imod(-1, 10));
        assert_eq!(-1, super::imod(-1, -10));
        assert_eq!(-2, super::imod(-12, -10));
        assert_eq!(0, super::imod(10, -10));
        assert_eq!(0, super::imod(10, 1));
    }

    #[test]
    #[should_panic(expected = "attempt to calculate the remainder with a divisor of zero")]
    fn test_imod_by_zero() {
        assert_eq!(0, super::imod(10, 0));
    }
}
