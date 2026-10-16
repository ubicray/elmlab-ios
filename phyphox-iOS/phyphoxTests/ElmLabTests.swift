//
//  ElmLabTests.swift
//  phyphoxTests
//
//  Elm Lab: the home screen golden, the Azerbaijani strings and the first-launch language rule.
//

import XCTest
import SnapshotTesting
@testable import phyphox

final class ElmLabTests: XCTestCase {
    ///Next to the view goldens, so the test workflow's re-rendered goldens include it
    private var snapshotDirectory: String {
        return DocsCorpus.repositoryRoot
            .appendingPathComponent("phyphox-iOS/phyphoxTests/Snapshots/views/elmlab-home", isDirectory: true)
            .path
    }

    //All cards, whatever this simulator's sensors: the golden pins the layout, not the device
    func testHomeScreenSnapshot() {
        for (name, width) in [("phone", CGFloat(390)), ("tablet", CGFloat(834))] {
            let home = ElmLabHomeView(sections: ElmLab.sections)
            home.frame = CGRect(x: 0, y: 0, width: width, height: 10000)
            home.layoutIfNeeded()
            let size = CGSize(width: width, height: home.contentSize.height)
            home.frame = CGRect(origin: .zero, size: size)
            home.layoutIfNeeded()

            let failure = verifySnapshot(
                of: home,
                as: .image(size: size, traits: UITraitCollection(displayScale: 2)),
                named: name,
                snapshotDirectory: snapshotDirectory,
                testName: "home")
            if let failure = failure {
                XCTFail("elmlab-home/\(name): \(failure)")
            }
        }
    }

    func testEveryCardHasItsPictureAndTexts() {
        for section in ElmLab.sections {
            XCTAssertNotEqual(localize(section.heading), section.heading, "no text for \(section.heading)")
            for card in section.cards {
                XCTAssertNotNil(UIImage(named: card.image), "no picture \(card.image)")
                XCTAssertNotEqual(localize(card.title), card.title, "no text for \(card.title)")
                XCTAssertNotEqual(localize(card.subtitle), card.subtitle, "no text for \(card.subtitle)")
            }
        }
    }

    func testAzerbaijaniLoads() throws {
        let path = try XCTUnwrap(Bundle.main.path(forResource: "az", ofType: "lproj"), "az.lproj is not in the app")
        let az = try XCTUnwrap(Bundle(path: path))
        XCTAssertEqual(az.localizedString(forKey: "cancel", value: nil, table: nil), "Ləğv et")
        XCTAssertEqual(az.localizedString(forKey: "elmlabSensorHeading", value: nil, table: nil), "Sensorlar")
    }

    func testAzerbaijaniIsTheDefaultOnlyOnAFreshLaunch() {
        let plain = ["/app"]
        XCTAssertTrue(ElmLab.shouldSetDefaultLanguage(alreadySet: false, appLanguages: nil, arguments: plain, environment: [:]))
        //Once only, so a later change in the system settings sticks
        XCTAssertFalse(ElmLab.shouldSetDefaultLanguage(alreadySet: true, appLanguages: nil, arguments: plain, environment: [:]))
        //The user already picked a language for the app
        XCTAssertFalse(ElmLab.shouldSetDefaultLanguage(alreadySet: false, appLanguages: ["ru"], arguments: plain, environment: [:]))
        //Tests and automation pin their own language
        XCTAssertFalse(ElmLab.shouldSetDefaultLanguage(alreadySet: false, appLanguages: nil, arguments: plain, environment: ["XCTestConfigurationFilePath": "x"]))
        XCTAssertFalse(ElmLab.shouldSetDefaultLanguage(alreadySet: false, appLanguages: nil, arguments: plain + ["-AppleLanguages", "(en)"], environment: [:]))
        XCTAssertFalse(ElmLab.shouldSetDefaultLanguage(alreadySet: false, appLanguages: nil, arguments: plain + ["-phyphoxUrl", "phyphox://x"], environment: [:]))
        XCTAssertFalse(ElmLab.shouldSetDefaultLanguage(alreadySet: false, appLanguages: nil, arguments: plain + ["screenshot"], environment: [:]))
    }
}
